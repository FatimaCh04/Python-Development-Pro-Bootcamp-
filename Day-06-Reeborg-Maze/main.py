import math

def paint(height,width,cover):

    area=height*width

    cans=math.ceil(area/cover)

    print(cans)

paint(5,4,5)