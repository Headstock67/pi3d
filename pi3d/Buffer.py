import ctypes, itertools

from ctypes import c_float, c_int

from echomesh.util import Log

from pi3d.constants import *
from pi3d.util import Utility
from pi3d.util.Loadable import Loadable
from pi3d.util.Ctypes import c_floats, c_shorts

LOGGER = Log.logger(__name__)

class Buffer(Loadable):
  """Holds the vertex, normals, incices and tex_coords for each part of
  a Shape that needs to be rendered with a different material or texture
  Shape holds an array of Buffer objects.

  """
  def __init__(self, shape, pts, texcoords, faces, normals=None, smooth=True):
    """Generate a vertex buffer to hold data and indices. If no normals
    are provided then these are generated.

    Arguments:
      *shape*
        Shape object that this Buffer is a child of
      *pts*
        array of vertices tuples i.e. [(x0,y0,z0), (x1,y1,z1),...]
      *texcoords*
        array of texture (uv) coordinates tuples
        i.e. [(u0,v0), (u1,v1),...]
      *faces*
        array of indices (of pts array) defining triangles
        i.e. [(a0,b0,c0), (a1,b1,c1),...]

    Keyword arguments:
      *normals*
        array of vector component tuples defining normals at each
        vertex i.e. [(x0,y0,z0), (x1,y1,z1),...]
      *smooth*
        if calculating normals then average normals for all faces
        meeting at this vertex, otherwise just use first (for speed).

    """
    super(Buffer, self).__init__()

    # Uniform variables all in one array!
    self.unib = (c_float * 12)(0.0, 0.0, 0.0,
                              0.5, 0.5, 0.5,
                              1.0, 1.0, 0.0,
                              0.0, 0.0, 0.0)
    """ pass to shader array of vec3 uniform variables:

    ===== ============================ ==== ==
    vec3        description            python
    ----- ---------------------------- -------
    index                              from to
    ===== ============================ ==== ==
        0  ntile, shiny, blend           0   2
        1  material                      3   5
        2  umult, vmult (only 2 used)    6   7
        3  u_off, v_off (only 2 used)    9  10
    ===== ============================ ==== ==
    """
    self.shape = shape

    if not normals:
      LOGGER.debug("Calculating normals ...")

      normals = [[] for p in pts]
      # Calculate normals.
      for f in faces:
        a, b, c = f[0:3]

        ab = Utility.vec_sub(pts[a], pts[b])
        bc = Utility.vec_sub(pts[a], pts[c])
        n = tuple(Utility.vec_normal(Utility.vec_cross(ab, bc)))
        for x in f[0:3]:
          normals[x].append(n)

      for i, n in enumerate(normals):
        if n:
          if smooth:
            norms = [sum(v[k] for v in n) for k in range(3)]
          else:  # This should be slightly faster for large shapes
            norms = [n[0][k] for k in range(3)]
          normals[i] = tuple(Utility.vec_normal(norms))
        else:
          normals[i] = 0, 0, 0.01

    # keep a copy for speeding up the collision testing of ElevationMap
    self.vertices = pts
    self.normals = normals
    self.tex_coords = texcoords
    self.indices = faces
    self.material = (0.5, 0.5, 0.5, 1.0)

    # Pack points,normals and texcoords into tuples and convert to ctype floats.
    points = [p + n + t for p, n, t in zip(pts, normals, texcoords)]
    self.array_buffer = c_floats(list(itertools.chain(*points)))

    self.ntris = len(faces)
    points = [f[0:3] for f in faces]
    self.element_array_buffer = c_shorts(list(itertools.chain(*points)))

  def re_init(self, shape, pts, texcoords, faces, normals=None, smooth=True):
    """Only reset the opengl buffer variables: vertices, tex_coords, indices
    normals (which is generated if not supplied) **NB this method will
    go horribly wrong if you change the size of the arrays supplied in
    the argument as the opengles buffers are reused** Arguments are
    as per __init__()"""
    tmp_unib = (c_float * 12)(self.unib[0], self.unib[1], self.unib[2],
                              self.unib[3], self.unib[4], self.unib[5],
                              self.unib[6], self.unib[7], self.unib[8],
                              self.unib[9], self.unib[10], self.unib[11])
    self.__init__(shape, pts, texcoords, faces, normals, smooth)
    opengles.glBufferData(GL_ARRAY_BUFFER,
                          ctypes.sizeof(self.array_buffer),
                          ctypes.byref(self.array_buffer),
                          GL_STATIC_DRAW)
    opengles.glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                          ctypes.sizeof(self.element_array_buffer),
                          ctypes.byref(self.element_array_buffer),
                          GL_STATIC_DRAW)
    self.opengl_loaded = True
    self.unib = tmp_unib

  def _load_opengl(self):
    self.vbuf = c_int()
    opengles.glGenBuffers(1, ctypes.byref(self.vbuf))
    self.ebuf = c_int()
    opengles.glGenBuffers(1, ctypes.byref(self.ebuf))
    self._select()
    opengles.glBufferData(GL_ARRAY_BUFFER,
                          ctypes.sizeof(self.array_buffer),
                          ctypes.byref(self.array_buffer),
                          GL_STATIC_DRAW)
    opengles.glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                          ctypes.sizeof(self.element_array_buffer),
                          ctypes.byref(self.element_array_buffer),
                          GL_STATIC_DRAW)

  def _select(self):
    """Makes our buffers active."""
    opengles.glBindBuffer(GL_ARRAY_BUFFER, self.vbuf)
    opengles.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebuf)

  def set_draw_details(self, shader, textures, ntiles=0.0, shiny=0.0,
                       umult=1.0, vmult=1.0):
    """Can be used to set information needed for drawing as a one off
    rather than sending as arguments to draw().

    Arguments:
      *shader*
        Shader object
      *textures*
        array of Texture objects

    Keyword arguments:
      *ntiles*
        multiple for tiling normal map which can be less than or greater
        than 1.0. 0.0 disables the normal mapping, float
      *shiny*
        how strong to make the reflection 0.0 to 1.0, float
      *umult*
        multiplier for tiling the texture in the u direction
      *vmult*
        multiplier for tiling the texture in the v direction
    """
    self.shader = shader
    self.shape.shader = shader # set shader for parent shape
    self.textures = textures # array of Textures
    self.unib[0] = ntiles
    self.unib[1] = shiny
    self.unib[6] = umult
    self.unib[7] = vmult

  def set_material(self, mtrl):
    self.unib[3:6] = mtrl[0:3]
    
  def set_offset(self, offset=(0.0, 0.0)):
    self.unib[9:11] = offset

  def draw(self, shader=None, textures=None, ntl=None, shny=None, fullset=True):
    """Draw this Buffer, called by the parent Shape.draw()

    Keyword arguments:
      *shader*
        Shader object
      *textures*
        array of Texture objects
      *ntl*
        multiple for tiling normal map which can be less than or greater
        than 1.0. 0.0 disables the normal mapping, float
      *shiny*
        how strong to make the reflection 0.0 to 1.0, float
    """
    self.load_opengl()

    shader = shader or self.shader
    textures = textures or self.textures
    if ntl:
      self.unib[0] = ntl
    if shny:
      self.unib[1] = shny
    self._select()

    opengles.glVertexAttribPointer(shader.attr_vertex, 3, GL_FLOAT, 0, 32, 0)
    opengles.glVertexAttribPointer(shader.attr_normal, 3, GL_FLOAT, 0, 32, 12)
    opengles.glVertexAttribPointer(shader.attr_texcoord, 2, GL_FLOAT, 0, 32, 24)
    opengles.glEnableVertexAttribArray(shader.attr_normal)
    opengles.glEnableVertexAttribArray(shader.attr_vertex)
    opengles.glEnableVertexAttribArray(shader.attr_texcoord)

    opengles.glDisable(GL_BLEND)

    self.unib[2] = 0.6
    for t, texture in enumerate(textures):
      opengles.glActiveTexture(GL_TEXTURE0 + t)
      assert texture.tex(), "There was an empty texture in your Buffer."
      opengles.glBindTexture(GL_TEXTURE_2D, texture.tex())

      opengles.glUniform1i(shader.unif_tex[t], t)

      if texture.blend:
        opengles.glEnable(GL_BLEND)
        # i.e. if any of the textures set to blend then all will for this shader.
        self.unib[2] = 0.05

    opengles.glUniform3fv(shader.unif_unib, 4, ctypes.byref(self.unib))
    opengles.glDrawElements(GL_TRIANGLES, self.ntris * 3, GL_UNSIGNED_SHORT, 0)
