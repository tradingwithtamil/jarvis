package main

import (
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

const (
	appVersion   = "1.0.0"
	installerURL = "https://raw.githubusercontent.com/tradingwithtamil/jarvis/a6a728a01be3fb3c93a7b9a358f849dd416ce1bb/commander/install-rd-windows.ps1"
	installerSHA = "a764da060c5ed16698ceb7a2a51b9b058ab4982a45d6cc46250490d1dd0c084f"
)

func isAdmin() bool {
	dll := syscall.NewLazyDLL("shell32.dll")
	proc := dll.NewProc("IsUserAnAdmin")
	r, _, _ := proc.Call()
	return r != 0
}

func elevate() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	verb, _ := syscall.UTF16PtrFromString("runas")
	file, _ := syscall.UTF16PtrFromString(exe)
	dir, _ := syscall.UTF16PtrFromString(filepath.Dir(exe))
	dll := syscall.NewLazyDLL("shell32.dll")
	proc := dll.NewProc("ShellExecuteW")
	r, _, callErr := proc.Call(
		0,
		uintptr(unsafe.Pointer(verb)),
		uintptr(unsafe.Pointer(file)),
		0,
		uintptr(unsafe.Pointer(dir)),
		1,
	)
	if r <= 32 {
		return fmt.Errorf("UAC elevation failed: %v", callErr)
	}
	return nil
}

func downloadInstaller(dst string) error {
	client := &http.Client{Timeout: 90 * time.Second}
	resp, err := client.Get(installerURL)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("installer download returned HTTP %d", resp.StatusCode)
	}
	f, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer f.Close()
	h := sha256.New()
	if _, err = io.Copy(io.MultiWriter(f, h), resp.Body); err != nil {
		return err
	}
	got := fmt.Sprintf("%x", h.Sum(nil))
	if !strings.EqualFold(got, installerSHA) {
		return fmt.Errorf("SHA256 mismatch: got %s", got)
	}
	return nil
}

func pause() {
	fmt.Println()
	fmt.Print("Press ENTER to close...")
	_, _ = fmt.Scanln()
}

func main() {
	fmt.Println("========================================")
	fmt.Printf(" RD Commander Setup v%s\n", appVersion)
	fmt.Println("========================================")
	if len(os.Args) > 1 && os.Args[1] == "--verify-only" {
		tmp := filepath.Join(os.TempDir(), "RDCommander-Verify.ps1")
		defer os.Remove(tmp)
		if err := downloadInstaller(tmp); err != nil {
			fmt.Println("VERIFY FAILED:", err)
			os.Exit(2)
		}
		fmt.Println("VERIFY PASS: Windows EXE + pinned installer download + SHA256")
		return
	}
	if !isAdmin() {
		fmt.Println("Requesting Administrator permission...")
		if err := elevate(); err != nil {
			fmt.Println("ERROR:", err)
			pause()
		}
		return
	}
	tmp := filepath.Join(os.TempDir(), "RDCommander-Setup.ps1")
	_ = os.Remove(tmp)
	fmt.Println("Downloading verified RD Commander installer...")
	if err := downloadInstaller(tmp); err != nil {
		fmt.Println("ERROR:", err)
		pause()
		return
	}
	defer os.Remove(tmp)
	fmt.Println("Installer SHA256 verified.")

	fmt.Println("Starting RD Commander enrollment...")
	cmd := exec.Command(
		"powershell.exe",
		"-NoProfile",
		"-ExecutionPolicy", "Bypass",
		"-File", tmp,
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		fmt.Println()
		fmt.Println("RD Commander setup failed:", err)
		pause()
		return
	}
	fmt.Println()
	fmt.Println("RD Commander setup completed successfully.")
	pause()
}
