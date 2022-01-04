for file in ./*.png
do
  cwebp -lossless -q 100 $file -o ${file%.png}.webp
done

