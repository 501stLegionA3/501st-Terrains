
#version: 0.01
#author: Scoob
#date: 2/15/2017
#function: batch file converter to create a .obj file for each .psk file in directory
#usage: python psk_to_obj.py C:/some_mesh_directory

import os, sys, struct

class psk_chunk:
  def __init__(self, data):
    self.id = data[:20].decode()
    self.header_data = data[20:32]
    self.type, self.size, self.count = struct.unpack('iii',self.header_data)
    self.body = b''
    self.header_size = 32
    en = self.header_size
    if self.type != 'ACTRHEAD' and self.count > 0:
      st = en
      en += self.size*self.count
      self.body = data[st:en]
      self.load_body()
    self.total_size = en

  def load_body(self):
    if self.id.startswith('PNTS0000'):
      body = self.body
      self.vtxs = []
      while len(body) > 0:
        head = body[:12]
        body = body[12:]
        self.vtxs.append(struct.unpack('fff',head))
    elif self.id.startswith('VTXW0000'):
      body = self.body
      self.wedges = []
      while len(body) > 0:
        head = body[:16]
        body = body[16:]
        if self.count <= 65536:
          self.wedges.append(struct.unpack('HxxffBxxx',head))
        else:
          self.wedges.append(struct.unpack('iffi',head))
    elif self.id.startswith('FACE0000'):
      body = self.body
      self.faces = []
      while len(body) > 0:
        head = body[:12]
        body = body[12:]
        self.faces.append(struct.unpack('HHHBBi',head))
    elif self.id.startswith('FACE0032'):
      body = self.body
      self.faces = []
      while len(body) > 0:
        head = body[:18]
        body = body[18:]
        self.faces.append(struct.unpack('iiiBBi',head))


class psk_file:
  def __init__(self, data):
    self.data = data
    self.chunks = []
    while len(data) > 0:
      t = psk_chunk(data)
      en = t.total_size
      self.chunks.append(t)
      data = data[en:]

  @classmethod
  def from_path(cls, file_path):
    assert type(file_path) is str and file_path.endswith('.psk')
    try:
      with open(file_path,'rb') as in_file:
        data = in_file.read()
    except FileNotFoundError as e:
      print('Error: file {} was not found'.format(file_path))
      raise
    return cls(data)

  def find_chunk(self, label):
    for chunk in self.chunks:
      if chunk.id.startswith(label):
        return chunk
    return None

  def get_vtxs(self):
    t = self.find_chunk('PNTS0000')
    if t is None:
      return None
    return t.vtxs

  def get_wedges(self):
    t = self.find_chunk('VTXW0000')
    if t is None:
      return None
    return t.wedges

  def get_faces(self):
    t = self.find_chunk('FACE0000')
    if t is None:
      return None
    return t.faces

  def get_faces32(self):
    t = self.find_chunk('FACE0032')
    if t is None:
      return None
    return t.faces


class obj_file:
  def __init__(self):
    self.vtxs = []
    self.coords = []
    self.normals = []
    self.faces = []

  @classmethod
  def from_psk(cls, in_psk):
    assert type(in_psk) is psk_file
    t = cls()

    t.vtxs = in_psk.get_vtxs()

    t.coords = [(x[1], x[2]) for x in in_psk.get_wedges()]

    p_map = [x[0] for x in in_psk.get_wedges()]

    t.faces = [((p_map[x[2]]+1,x[2]+1), (p_map[x[1]]+1,x[1]+1), (p_map[x[0]]+1,x[0]+1)) for x in in_psk.get_faces()]

    return t

  def __str__(self):
    out_str = ''

    out_str += '\n# Vertices\n'
    for vtx in self.vtxs:
      out_str += 'v {} {} {}\n'.format(*vtx)

    out_str += '\n# UVs\n'
    for uv in self.coords:
      out_str += 'vt {} {}\n'.format(*uv)

    out_str += '\n# Faces\n'
    for face in self.faces:
      out_str += 'f {}/{} {}/{} {}/{}\n'.format(face[0][0], face[0][1], face[1][0], face[1][1], face[2][0], face[2][1])

    return out_str

  def save_as(self, file_path):
    assert type(file_path) is str and file_path.endswith('.obj')
    try:
      with open(file_path,'w') as out_file:
        out_file.write(str(self))
    except FileNotFoundError as e:
      print('Error: file {} was not found'.format(file_path))
      raise

      
def convert_psk_to_fbx(file_path):
  in_file = psk_file.from_path(file_path)
  print('Loaded {} successfully'.format(file_path))

  out_file = obj_file.from_psk(in_file)
  print('Converted {} successfully to obj intermediate format'.format(file_path))

  out_file.save_as(file_path[:-4]+'.obj')
  print('Saved to obj text format as {}'.format(file_path[:-4]+'.obj'))

  
def batch_convert_psk_to_fbx(dir_path):
  assert type(dir_path) is str
  if not  os.path.isdir(dir_path):
    print('Error: no directory \'{}\' found'.format(dir_path))
    return
  d = dir_path
  jn = os.path.join
  files = [jn(d,x) for x in os.listdir(d) if os.path.isfile(jn(d,x)) and x.endswith('.psk')]
  for file in files:
    convert_psk_to_fbx(file)

    
if __name__ == '__main__':
  dir_path = '.'
  if len(sys.argv) >= 2:
    dir_path = sys.argv[1]
  batch_convert_psk_to_fbx(dir_path)

psk_to_obj.py
Displaying psk_to_obj.py.