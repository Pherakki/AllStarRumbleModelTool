import struct
from PXBIReader import PXBIReadWriter


class PXBIInterface:
    """
    Only contains the 'important' data from the reader - drops file pointers,
    counts, etc.
    
    If rebuilding the file, this class should calculate the required pointers
    and counts and pass those on to a ReadWriter instance.
    """
    def __init__(self):
        self.meshes = None
    
    @classmethod
    def from_file(cls, file):
        instance = cls()
        with open(file, 'rb') as F:
            rdr = PXBIReadWriter(F)
            rdr.read()
            
        instance.meshes = [MeshInterface(mesh) for mesh in rdr.meshes]
        instance.materials = [MaterialInterface(material) for material in rdr.materials]
        instance.texture_names = rdr.texture_names
        instance.texture_data = [convert_gtf_to_dds(data) for data in rdr.texture_binary]
        instance.texture_data_raw = [data for data in rdr.texture_binary]
        instance.bone_data = rdr.bone_data
        instance.joint_data = rdr.joint_data
        instance.joint_names = rdr.joint_names
        
        return instance
        
class MeshInterface:
    def __init__(self, mesh):
        self.name = mesh.name
        self.vertices = mesh.vertex_data
        self.triangles = mesh.triangles
        self.material_index = mesh.some_id
        
class MaterialInterface:
    def __init__(self, material):
        self.name = material.name
        self.assigned_textures = material.assigned_textures
        
        
def build_dds_header(height, width, size, depth, nmipmaps, dds_codec, flag):
                  #<-------- MAGIC VALUE --------->#  #<----- HEADER SIZE (124) ------>#  #<--------- DDS FLAGS ---------->#
    dds_header = [b'\x44', b'\x44', b'\x53', b'\x20', b'\x7c', b'\x00', b'\x00', b'\x00', b'\x07', b'\x10', b'\x00', b'\x00']
    dds_header.append(struct.pack('I', height))
    dds_header.append(struct.pack('I', width))
    dds_header.append(struct.pack('I', size))
    dds_header.append(struct.pack('I', depth))
    dds_header.append(struct.pack('I', nmipmaps))

                       #<--------------------------------------------------------------- RESERVED ----------------------------------------------------------------->#
    dds_header.extend([b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                       b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                       b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', 
              
                      ################
                      # PIXEL FORMAT #
                      ################
                      # STRUCTURE SIZE
                      b'\x20', b'\x00', b'\x00', b'\x00',
                      #<-------- PXF FLAGS -------->#  #< COMPRESSION FORMAT >#   #<-------- RGB BITCOUNT -------->#
                      flag, b'\x00', b'\x00', b'\x00', dds_codec,                 b'\x20', b'\x00', b'\x00', b'\x00', 
                      #<-------- RED BITMASK --------->#  #<------- GREEN BITMASK -------->#  #<------- BLUE BITMASK --------->#  #<------- ALPHA BITMASK -------->#
                      b'\x00', b'\x00', b'\xff', b'\x00', b'\x00', b'\xff', b'\x00', b'\x00', b'\xff', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\xff', 
                      #<----------- CAPS 1 ----------->#  #<----------- CAPS 2 ----------->#  #<----------- CAPS 3 ----------->#  #<----------- CAPS 4 ----------->#
                      b'\x00', b'\x10', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                      #<---------- RESERVED ---------->#
                      b'\x00', b'\x00', b'\x00', b'\x00'])

    return b''.join(dds_header)

dds_codices = {166: 'DXT1'.encode('ascii'),
               133: b''.join([b'\x00', b'\x00', b'\x00', b'\x00']),
               134: 'DXT1'.encode('ascii'),
               136: 'DXT5'.encode('ascii')}

pxf_flags = {166: b'\x04',
             133: b'\x41',
             134: b'\x04',
             136: b'\x04'}

def convert_gtf_to_dds(gtf_data):
    codec = gtf_data[24]
    w = struct.unpack('>H', gtf_data[32:34])[0]
    h = struct.unpack('>H', gtf_data[34:36])[0]
    depth = struct.unpack('>H', gtf_data[36:38])[0]
    
    dds_codec = dds_codices[codec]
    flag = pxf_flags[codec]
    
    return build_dds_header(h, w, h*w, depth, 4, dds_codec, flag) + gtf_data[128:]