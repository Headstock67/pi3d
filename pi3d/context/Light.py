from echomesh.util.DefaultInstance import DefaultInstance

class Light(DefaultInstance):
  """ Holds information about lighting to be used in shaders """
  def __init__(self,
               lightpos=(10, -10, 20),
               lightcol=(1.0, 1.0, 1.0),
               lightamb=(0.1, 0.1, 0.2)):
    """ set light values. These are set in Shape.unif as part of the Shape
    constructor. They can be changed using Shape.set_light()
    The pixel shade is calculated by componet multiplying lightcol by the
    texture by the dot product of direction and -normal + component multiplying
    lightamb by the texture
    
    Arguments:
    lightpos -- tuple (x,y,z) vector direction *from* the light
    lightcol -- tuple (r,g,b) defines shade and brightness
    lightamb -- tuple (r,g,b) ambient lighting multiplier
    """
    super(Light, self).__init__()
    self.lightpos = lightpos
    self.lightcol = lightcol
    self.lightamb = lightamb

  def position(self, lightpos):
    self.lightpos = lightpos

  def color(self, lightcol):
    self.lightcol = lightcol

  def ambient(self, lightamb):
    self.lightamb = lightamb

  @staticmethod
  def _default_instance():
    return Light()

