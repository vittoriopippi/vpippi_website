from django.db import models
import os
from PIL import Image
import numpy as np

def upload_map(instance, filename):
    ext = filename.split('.')[-1]
    name = instance.name.replace(' ', '_')
    return os.path.join('game/maps', f'{name}.{ext}')

def upload_walls(instance, filename):
    ext = filename.split('.')[-1]
    name = instance.name.replace(' ', '_')
    return os.path.join('game/walls', f'{name}.{ext}')

def upload_sprites(instance, filename):
    ext = filename.split('.')[-1]
    name = instance.name.replace(' ', '_')
    return os.path.join('game/players', f'{name}.{ext}')


class Map(models.Model):
    name = models.CharField(max_length=64, unique=True)
    origin_x = models.IntegerField(default=0)
    origin_y = models.IntegerField(default=0)
    origin_orientation = models.IntegerField(default=0, choices=[(0, "North"), (1, "East"), (2, "South"), (3, "West")])
    img = models.ImageField(upload_to=upload_map)
    walls_img = models.ImageField(upload_to=upload_walls)
    walls_array = models.TextField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.width = self.walls_img.width if self.width is None else self.width
        self.height = self.walls_img.height if self.height is None else self.height
        
        walls_img = Image.open(self.walls_img)
        walls_img = walls_img.convert('L')
        walls_img = walls_img.resize((self.width, self.height), Image.NEAREST)
        walls_img = np.array(walls_img) > 0
        walls_array = np.array(walls_img, dtype=np.uint8)
        self.walls_array = str(walls_array.tolist()).replace(' ', '')

        super(Map, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Interaction(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    text = models.CharField(max_length=280)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.map.name} [{self.x},{self.y}]'
    
class Door(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    dst_map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='dst_map')
    dst_x = models.IntegerField(default=0)
    dst_y = models.IntegerField(default=0)
    dst_orientation = models.IntegerField(default=0, choices=[(0, "North"), (1, "East"), (2, "South"), (3, "West")])

    def __str__(self):
        return self.name
    
class Player(models.Model):
    name = models.CharField(max_length=64, unique=True)
    spritesheet = models.ImageField(upload_to=upload_sprites)

    def __str__(self):
        return self.name
