
# import the Python Image  
# processing Library 
from PIL import Image 
import math
  
# Giving The Original image Directory  
# Specified 
image_name = "index.png"
Original_Image = Image.open(f"./{image_name}") 


# Rotation only, 1rpm at 15fps
# for i in range(0, 900):
#   rotated_image = Original_Image.rotate(i*0.4) 
#   rotated_image.save(f"./animation2/{i}.png") 
#   print(f"Rotated {i*0.4} degrees")


# Translation only, 1rpm at 15fps
for i in range(450, -450, -1):

  # translation_distance = 225
  translation_distance = 90

  # angle = (900-i + 900/2)*0.4
  # angle = (900-i + 900/2)*0.4
  angle = i*0.4

  x = translation_distance * math.sin(math.radians(angle))
  y = translation_distance * math.cos(math.radians(angle))


  zoomed_image = Original_Image.resize((int(Original_Image.size[0]*1.5), int(Original_Image.size[1]*1.5)))
  # zoomed_image.save(f"./translation/-1.png")

  window_size = 360

  # print(f"Angle: {round(angle, 2)}, x: {round(x,2)}, y: {round(y, 2)}")

  translated_image = zoomed_image.crop((zoomed_image.size[0]/2 - window_size/2 + x, zoomed_image.size[1]/2 - window_size/2 + y, zoomed_image.size[0]/2 + window_size/2 + x, zoomed_image.size[1]/2 + window_size/2 + y))

  # translated_image = Original_Image.transform(Original_Image.size, Image.AFFINE, (1, 0, x, 0, 1, y))

  resized_image = translated_image.resize((360, 360))

  out_name = abs(i-450)

  resized_image.save(f"./translation/{out_name}.png")
  print(f"Translated {out_name} degrees, image dimensions: {resized_image.size}")


