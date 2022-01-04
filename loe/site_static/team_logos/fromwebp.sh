for file in ./*.webp
do
  dwebp $file -o ${file%.webp}.png
done

