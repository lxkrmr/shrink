package main

import (
	"flag"
	"fmt"
	"image"
	"image/jpeg"
	"image/png"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/image/draw"
)

const version = "0.2.0"

var supportedExts = map[string]bool{
	".png":  true,
	".jpg":  true,
	".jpeg": true,
}

// targetSize returns the dimensions an image should be scaled to in order to
// fit within maxW x maxH while preserving the aspect ratio. Returns the
// original dimensions if the image already fits.
func targetSize(w, h, maxW, maxH int) (int, int) {
	scaleW, scaleH := 1.0, 1.0
	if maxW > 0 && w > maxW {
		scaleW = float64(maxW) / float64(w)
	}
	if maxH > 0 && h > maxH {
		scaleH = float64(maxH) / float64(h)
	}
	scale := min(scaleW, scaleH)
	if scale >= 1.0 {
		return w, h
	}
	return max(1, int(float64(w)*scale)), max(1, int(float64(h)*scale))
}

func fmtBytes(b int64) string {
	switch {
	case b >= 1024*1024:
		return fmt.Sprintf("%.1f MB", float64(b)/1024/1024)
	case b >= 1024:
		return fmt.Sprintf("%d KB", b/1024)
	default:
		return fmt.Sprintf("%d B", b)
	}
}

func loadImage(path string) (image.Image, string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, "", err
	}
	defer f.Close()
	return image.Decode(f)
}

func saveImage(path string, img image.Image, format string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	switch format {
	case "jpeg":
		return jpeg.Encode(f, img, &jpeg.Options{Quality: 85})
	case "png":
		return png.Encode(f, img)
	default:
		return fmt.Errorf("unsupported format: %s", format)
	}
}

func scaleImage(src image.Image, w, h int) image.Image {
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	draw.CatmullRom.Scale(dst, dst.Bounds(), src, src.Bounds(), draw.Over, nil)
	return dst
}

func fileSize(path string) (int64, error) {
	info, err := os.Stat(path)
	if err != nil {
		return 0, err
	}
	return info.Size(), nil
}

func run(dir string, maxW, maxH int) int {
	entries, err := os.ReadDir(dir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 1
	}

	resized, ok, failed := 0, 0, 0

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		ext := strings.ToLower(filepath.Ext(entry.Name()))
		if !supportedExts[ext] {
			continue
		}

		path := filepath.Join(dir, entry.Name())

		sizeBefore, err := fileSize(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: error: %v\n", entry.Name(), err)
			failed++
			continue
		}

		img, format, err := loadImage(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: error: %v\n", entry.Name(), err)
			failed++
			continue
		}

		b := img.Bounds()
		w, h := b.Dx(), b.Dy()
		tw, th := targetSize(w, h, maxW, maxH)

		if tw == w && th == h {
			fmt.Printf("%s: ok (%dx%d)\n", entry.Name(), w, h)
			ok++
			continue
		}

		scaled := scaleImage(img, tw, th)
		if err := saveImage(path, scaled, format); err != nil {
			fmt.Fprintf(os.Stderr, "%s: error: %v\n", entry.Name(), err)
			failed++
			continue
		}

		sizeAfter, _ := fileSize(path)
		fmt.Printf("%s: %dx%d → %dx%d (%s → %s)\n",
			entry.Name(), w, h, tw, th,
			fmtBytes(sizeBefore), fmtBytes(sizeAfter),
		)
		resized++
	}

	fmt.Printf("\n%d resized, %d ok, %d failed\n", resized, ok, failed)
	if failed > 0 {
		return 1
	}
	return 0
}

func main() {
	var maxWidth, maxHeight int
	var showVersion bool

	flag.IntVar(&maxWidth, "max-width", 0, "maximum width in pixels")
	flag.IntVar(&maxHeight, "max-height", 0, "maximum height in pixels")
	flag.BoolVar(&showVersion, "version", false, "print version and exit")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "maxsize %s\n\nUsage: maxsize --max-width N --max-height N <dir>\n\n", version)
		flag.PrintDefaults()
	}
	flag.Parse()

	if showVersion {
		fmt.Println(version)
		return
	}
	if flag.NArg() != 1 {
		flag.Usage()
		os.Exit(1)
	}
	if maxWidth == 0 && maxHeight == 0 {
		fmt.Fprintln(os.Stderr, "error: at least one of --max-width or --max-height is required")
		os.Exit(1)
	}

	dir := flag.Arg(0)
	info, err := os.Stat(dir)
	if err != nil || !info.IsDir() {
		fmt.Fprintf(os.Stderr, "error: not a directory: %s\n", dir)
		os.Exit(1)
	}

	os.Exit(run(dir, maxWidth, maxHeight))
}
