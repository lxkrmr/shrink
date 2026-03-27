package main

import (
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

// --- targetSize ---

func TestTargetSize(t *testing.T) {
	tests := []struct {
		name             string
		w, h, maxW, maxH int
		wantW, wantH     int
	}{
		{"no limits", 1000, 500, 0, 0, 1000, 500},
		{"already fits", 800, 600, 1280, 1280, 800, 600},
		{"exact limit", 1280, 960, 1280, 1280, 1280, 960},
		{"width is limiting factor", 3200, 2400, 1280, 1280, 1280, 960},
		{"height is limiting factor", 1920, 2400, 1280, 1280, 1024, 1280},
		{"only max-width set", 3200, 2400, 1280, 0, 1280, 960},
		{"only max-height set", 3200, 2400, 0, 1280, 1706, 1280},
		{"portrait image", 1000, 2000, 1280, 1280, 640, 1280},
		{"tiny image stays tiny", 10, 10, 1280, 1280, 10, 10},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotW, gotH := targetSize(tt.w, tt.h, tt.maxW, tt.maxH)
			if gotW != tt.wantW || gotH != tt.wantH {
				t.Errorf("targetSize(%d,%d,%d,%d) = (%d,%d), want (%d,%d)",
					tt.w, tt.h, tt.maxW, tt.maxH, gotW, gotH, tt.wantW, tt.wantH)
			}
		})
	}
}

// --- fmtBytes ---

func TestFmtBytes(t *testing.T) {
	tests := []struct {
		in   int64
		want string
	}{
		{500, "500 B"},
		{1024, "1 KB"},
		{2048, "2 KB"},
		{1024 * 1024, "1.0 MB"},
		{4404019, "4.2 MB"},
	}
	for _, tt := range tests {
		got := fmtBytes(tt.in)
		if got != tt.want {
			t.Errorf("fmtBytes(%d) = %q, want %q", tt.in, got, tt.want)
		}
	}
}

// --- integration ---

func makePNG(t *testing.T, path string, w, h int) {
	t.Helper()
	img := image.NewRGBA(image.Rect(0, 0, w, h))
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			img.Set(x, y, color.RGBA{R: uint8(x % 256), G: uint8(y % 256), B: 128, A: 255})
		}
	}
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	if err := png.Encode(f, img); err != nil {
		t.Fatal(err)
	}
}

func imageDims(t *testing.T, path string) (int, int) {
	t.Helper()
	f, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	img, _, err := image.Decode(f)
	if err != nil {
		t.Fatal(err)
	}
	b := img.Bounds()
	return b.Dx(), b.Dy()
}

func TestRun_ResizesLargeImage(t *testing.T) {
	dir := t.TempDir()
	makePNG(t, filepath.Join(dir, "large.png"), 3200, 2400)

	code := run(dir, 1280, 1280)
	if code != 0 {
		t.Fatalf("run returned %d, want 0", code)
	}

	w, h := imageDims(t, filepath.Join(dir, "large.png"))
	if w != 1280 || h != 960 {
		t.Errorf("got %dx%d, want 1280x960", w, h)
	}
}

func TestRun_SkipsSmallImage(t *testing.T) {
	dir := t.TempDir()
	makePNG(t, filepath.Join(dir, "small.png"), 800, 600)

	stat1, _ := os.Stat(filepath.Join(dir, "small.png"))
	code := run(dir, 1280, 1280)
	if code != 0 {
		t.Fatalf("run returned %d, want 0", code)
	}
	stat2, _ := os.Stat(filepath.Join(dir, "small.png"))

	if stat1.ModTime() != stat2.ModTime() {
		t.Error("small.png was modified but should have been skipped")
	}
}

func TestRun_MixedDir(t *testing.T) {
	dir := t.TempDir()
	makePNG(t, filepath.Join(dir, "big.png"), 3200, 2400)
	makePNG(t, filepath.Join(dir, "small.png"), 640, 480)

	code := run(dir, 1280, 1280)
	if code != 0 {
		t.Fatalf("run returned %d, want 0", code)
	}

	w, h := imageDims(t, filepath.Join(dir, "big.png"))
	if w != 1280 || h != 960 {
		t.Errorf("big.png: got %dx%d, want 1280x960", w, h)
	}
	w, h = imageDims(t, filepath.Join(dir, "small.png"))
	if w != 640 || h != 480 {
		t.Errorf("small.png: got %dx%d, want 640x480 (should not be resized)", w, h)
	}
}

func TestRun_EmptyDir(t *testing.T) {
	dir := t.TempDir()
	code := run(dir, 1280, 1280)
	if code != 0 {
		t.Fatalf("run returned %d, want 0", code)
	}
}

func TestRun_IgnoresNonImages(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "notes.txt"), []byte("hello"), 0644); err != nil {
		t.Fatal(err)
	}
	code := run(dir, 1280, 1280)
	if code != 0 {
		t.Fatalf("run returned %d, want 0", code)
	}
}

// --- benchmarks ---

func BenchmarkTargetSize(b *testing.B) {
	for b.Loop() {
		targetSize(3200, 2400, 1280, 1280)
	}
}

func BenchmarkScaleImage(b *testing.B) {
	src := image.NewRGBA(image.Rect(0, 0, 3200, 2400))
	b.ResetTimer()
	for b.Loop() {
		scaleImage(src, 1280, 960)
	}
}
