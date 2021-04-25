for file in ./*.png
do
  cwebp -lossless -q 100 $file -o webp/${file%.png}.webp
done

