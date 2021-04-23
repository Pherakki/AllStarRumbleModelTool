from BaseRW import BaseRW
import struct

class PXBIReadWriter(BaseRW):
    def __init__(self, F):
        super().__init__(F)
        self.offset = 64
        self.mesh_pointers = None
        self.meshes = None
        self.materials = None
        self.bone_data = []
        self.joint_names = []
        self.texture_names = []
        self.texture_binary = []
    
    def read(self):
        self.read_write(self.read_buffer, self.read_raw, self.read_ascii, "read", self.cleanup_ragged_chunk_read, self.prepare_read_operation)
        self.interpret_data()
    
    def read_write(self, rw_operator, rw_operator_raw, rw_ascii_operator, rw_method_name, chunk_cleanup_operator, preparation_operator):
        self.rw_header(rw_operator, rw_ascii_operator)
        preparation_operator()
        self.rw_mesh_pointers(rw_operator)
        self.rw_meshes(rw_method_name, chunk_cleanup_operator)
        self.rw_material_pointers(rw_operator)
        self.rw_materials(rw_method_name)
        self.rw_bone_matrix_pointers(rw_operator)
        self.rw_bone_matrices(rw_operator)
        self.rw_joints(rw_operator)
        self.rw_texture_pointers(rw_operator)
        self.rw_strings(rw_operator)
        self.rw_pointer_list(rw_operator)
        self.rw_textures_header(rw_operator)
        self.rw_textures(rw_operator_raw)
        self.check_eof()
        
    def rw_header(self, rw_operator, rw_ascii_operator):
        rw_ascii_operator("filetype", 4)
        rw_operator("contents_size", "I", endianness=">")  # (?) Mising 64 bytes from total file size
        rw_operator("unknown_0x08", "I", endianness=">")  # Number of subreaders?
        rw_ascii_operator("next_filetype", 4)
        
        rw_operator("always_64", "I", endianness=">") # File pointer offset?
        rw_operator("file_mesh_names_pointer", "I", endianness=">")
        rw_operator("materials_bones_names_pointer", "I", endianness=">")
        rw_operator("unknown_bytecount_2", "I", endianness=">")  ############
        self.assert_equal("always_64", 64)
        
        rw_operator("pointer_list_pointer", "I", endianness=">")
        rw_operator("pointer_list_size", "I", endianness=">")
        rw_operator("textures_pointer", "I", endianness=">")
        rw_operator("end_of_file_pointer", "I", endianness=">")
        
        rw_operator("padding_0x30", "I", endianness=">")
        rw_operator("padding_0x34", "I", endianness=">")
        rw_operator("padding_0x38", "I", endianness=">")
        rw_operator("padding_0x3C", "I", endianness=">")
        self.assert_is_zero("padding_0x30")
        self.assert_is_zero("padding_0x34")
        self.assert_is_zero("padding_0x38")
        self.assert_is_zero("padding_0x3C")
        
        rw_operator("always_3", "I", endianness=">")  ############
        rw_operator("always_52", "I", endianness=">")  # Pointer to mesh header pointer....?
        rw_operator("padding_0x48", "I", endianness=">")
        rw_operator("padding_pointer", "I", endianness=">")
        self.assert_equal("always_3", 3)
        self.assert_equal("always_52", 52)
        self.assert_is_zero("padding_0x48")
        
        rw_operator("texture_count", "I", endianness=">")
        rw_operator("texture_pointers_pointer", "I", endianness=">")
        rw_operator("unknown_pointer_9", "I", endianness=">")  #############
        rw_operator("padding_0x5C", "I", endianness=">")
        self.assert_is_zero("padding_0x5C")
        
        rw_operator("padding_0x60", "I", endianness=">")
        rw_operator("padding_0x64", "I", endianness=">")
        rw_operator("padding_0x68", "I", endianness=">")
        rw_operator("padding_0x6C", "I", endianness=">")
        self.assert_is_zero("padding_0x60")
        self.assert_is_zero("padding_0x64")
        self.assert_is_zero("padding_0x68")
        self.assert_is_zero("padding_0x6C")
        
        rw_operator("padding_0x70", "I", endianness=">")
        rw_operator("always_68", "I", endianness=">")  # Mesh header pointer?
        rw_operator("material_count", "I", endianness=">")
        rw_operator("material_pointers_pointer", "I", endianness=">")
        self.assert_is_zero("padding_0x70")
        self.assert_equal("always_68", 68)  # If it's always 68, it might be a pointer to the mesh header...
        
        rw_operator("bone_pointers_pointer", "I", endianness=">")
        rw_operator("mesh_count", "I", endianness=">") # nmeshes
        rw_operator("mesh_pointers_pointer", "I", endianness=">") # Missing 64 bytes
        
        
    def prepare_read_operation(self):
        self.meshes = [MeshReadWrite(self.bytestream) for _ in range(self.mesh_count)]
        self.materials = [MaterialReadWrite(self.bytestream) for _ in range(self.material_count)]
        
    def rw_mesh_pointers(self, rw_operator):
        self.assert_file_pointer_now_at(self.mesh_pointers_pointer + self.offset)
        rw_operator("mesh_pointers", "I"*self.mesh_count, endianness='>')
        
    def rw_meshes(self, rw_method_name, chunk_cleanup_operator):
        for rdr, ptr in zip(self.meshes, self.mesh_pointers):
            self.assert_file_pointer_now_at(ptr + self.offset)
            getattr(rdr, rw_method_name)()
        chunk_cleanup_operator(self.bytestream.tell(), 4)
        
    def rw_material_pointers(self, rw_operator):
        self.assert_file_pointer_now_at(self.material_pointers_pointer + self.offset)
        rw_operator("material_pointers", "I"*self.material_count, endianness='>')
        
    def rw_materials(self, rw_method_name):
        for material, ptr in zip(self.materials, self.material_pointers):
            self.assert_file_pointer_now_at(ptr + self.offset)
            getattr(material, rw_method_name)()
        self.bytestream.seek(self.bone_pointers_pointer + self.offset)
    
    def rw_bone_matrix_pointers(self, rw_operator):
        self.assert_file_pointer_now_at(self.bone_pointers_pointer + self.offset)
        rw_operator("skeleton_name_pointer", 'I', endianness='>')
        rw_operator("bone_count", 'I', endianness='>')
        rw_operator("bone_matrices_pointer", 'I', endianness='>')
        rw_operator("joint_count", 'I', endianness='>')
        
    def rw_bone_matrices(self, rw_operator):
        if self.bone_matrices_pointer != 0:
            self.assert_file_pointer_now_at(self.bone_matrices_pointer + self.offset - 4)
            rw_operator("bone_data", "IIffffffffffffffff"*self.bone_count, endianness='>')
        
    def rw_joints(self, rw_operator):
        rw_operator("joint_list_name", "I", endianness='>')
        rw_operator("joint_data", "hhhhhhhhhhIIfffffffff"*self.joint_count, endianness='>')
        
    def rw_texture_pointers(self, rw_operator):
        self.assert_file_pointer_now_at(self.padding_pointer + self.offset)
        rw_operator("unknown_0x00", "I", endianness='>')  # 0 or 1?
        rw_operator("unknown_texture_pointer", "I", endianness='>')  # 16306496
        if self.unknown_texture_pointer != 0:
            self.assert_file_pointer_now_at(self.unknown_texture_pointer + self.offset)
            print(self.bytestream.read(64))


        self.assert_file_pointer_now_at(self.texture_pointers_pointer + self.offset)
        rw_operator("texture_pointers", "I"*self.texture_count, endianness='>')  # Points to the texture pointer info
        rw_operator("texture_pointer_info", "IIII"*self.texture_count, endianness='>') # File number, filepath, size, offset

    def rw_strings(self, rw_operator):
        # Just skip the strings
        self.assert_file_pointer_now_at(self.file_mesh_names_pointer + self.offset)
        self.bytestream.seek(self.pointer_list_pointer + self.offset)
        
    def rw_pointer_list(self, rw_operator):
        self.bytestream.seek(self.pointer_list_pointer + self.offset)
        num_to_read = (self.pointer_list_size - self.offset) // 4
        rw_operator("pointer_list", 'I'*num_to_read, endianness='>')
        
    def rw_textures_header(self, rw_operator):
        self.bytestream.seek(self.textures_pointer)
        rw_operator("num_textures_2", 'I', endianness='>')
        rw_operator("textures_header", 'I'*2*self.texture_count, endianness='>')  # This is a repeat of 'texture_pointer_info'

    def rw_textures(self, rw_operator_raw):
        """
        This needs to be changed to be read-write agnostic too if files are to be writable in the future, I'm just lazy
        """
        for size, rel_ptr in zip(self.textures_header[::2], self.textures_header[1::2]):
            ptr = rel_ptr + self.textures_pointer
            self.assert_file_pointer_now_at(ptr)
            self.texture_binary.append(self.bytestream.read(size))

    def check_eof(self):
        self.assert_file_pointer_now_at(self.end_of_file_pointer + self.textures_pointer)
        # If we're in read-mode, get next byte, which should not exist
        eof = b''
        try:
            eof = self.bytestream.read(1)
        except:
            pass
        if eof != b'':
            raise Exception("Not at the end of the file!")
            
    def interpret_data(self):
        """
        Takes the raw data read from a file and turns it into something that is more human-readable.
        Should be the inverse of 'reinterpret_data', which should be called before writing the file.
        """
        bone_matrix_data = []
        for chunk in chunks(self.bone_data, 18):
            ptr_1 = chunk[0]
            if ptr_1 != 0:
                name_1 = read_string_inplace(self.bytestream, ptr_1 + self.offset)
            else:
                name_1 = ''
            idx = chunk[1]  # Parent idx?

            matrix = [chunk[2:6], chunk[6:10], chunk[10:14], chunk[14:18]]
            bone_matrix_data.append([name_1, idx, matrix])
        self.bone_data = bone_matrix_data
        self.joint_data = list(chunks(self.joint_data, 21))
        self.joint_names = [read_string_inplace(self.bytestream, data[10]+self.offset) for data in self.joint_data]
        
        for file_ptr, name_ptr in zip(self.texture_pointer_info[::4], self.texture_pointer_info[1::4]):
            self.texture_names.append((read_string_inplace(self.bytestream, file_ptr+self.offset),
                                       read_string_inplace(self.bytestream, name_ptr+self.offset)))
            
class MeshReadWrite(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)
        self.name = None
        self.offset = 64
        
    def read(self):
        self.read_write(self.read_buffer, self.read_ascii, self.cleanup_ragged_chunk_read)
        self.interpret_data()
    
    def read_write(self, rw_operator, rw_ascii_operator, cleanup_chunk_operator):
        self.rw_header(rw_operator, rw_ascii_operator)
        self.rw_vertex_data(rw_operator)
        self.rw_triangles(rw_operator)
        cleanup_chunk_operator(self.bytestream.tell() + self.offset, 4)
        
    def rw_header(self, rw_operator, rw_ascii_operator):
        rw_operator("name_pointer", "I", endianness=">")
        rw_operator("unknown_bytecount_1", "I", endianness=">")
        rw_operator("some_id", "I", endianness=">")  # Material ID?
        rw_operator("unknown_bytecount_2", "I", endianness=">")
        rw_operator("bytes_per_vertex", "I", endianness=">")
        
        rw_operator("vertex_count", "I", endianness=">")
        rw_operator("vertices_pointer", "I", endianness=">") # Meshes ptr - 64
        rw_operator("triangle_count", "I", endianness=">")
        rw_operator("triangles_pointer", "I", endianness=">") # Triangles ptr - 64
        
    def rw_vertex_data(self, rw_operator):
        rw_operator("vertex_data", 'f'*(self.vertex_count*(self.bytes_per_vertex//4)), endianness='>')
        
    def rw_triangles(self, rw_operator):
        rw_operator("triangles", self.triangle_count*'H', endianness='>')
        
    def interpret_data(self):
        self.name = read_string_inplace(self.bytestream, self.name_pointer + self.offset)
        assert self.bytes_per_vertex == 88, "Bytes per vertex not 88."
        interpreted_vertex_data = []
        for chunk in chunks(self.vertex_data, 22):
            vertex = {}
            vertex['Position'] = chunk[0:3]
            vertex['Normal'] = chunk[3:6]
            vertex['UV'] = chunk[6:8]
            vertex['Tangent'] = chunk[8:11]
            vertex['Binormal'] = chunk[11:14]
            vertex['Weights'] = chunk[14:18]
            vertex['BoneIndices'] = chunk[18:22]
            interpreted_vertex_data.append(vertex)
        self.vertex_data = interpreted_vertex_data
        self.triangles = list(chunks(self.triangles, 3))
        
    def reinterpret_data(self):
        self.triangles = self.flatten_list(self.triangles)
        vertex_data = []
        for vertex in self.vertex_data:
            vertex_data.extend(vertex['Position'])
            vertex_data.extend(vertex['Normal'])
            vertex_data.extend(vertex['UV'])
            vertex_data.extend(vertex['Tangent'])
            vertex_data.extend(vertex['Binormal'])
            vertex_data.extend(vertex['Weights'])
            vertex_data.extend(vertex['BoneIndices'])
            
class MaterialReadWrite(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)
        self.offset = 64
        
        self.name_pointer = None
        self.name = None
        self.unknown_0x04 = None
        self.unknown_0x08 = None
        self.padding_0x0A = None
        
        self.unknown_floats_1 = None
        self.texture_count = None
        self.texture_assignment_pointer = None
        self.unknown_floats_2 = None
        
        self.texture_pointers = []
        self.assigned_textures = []

    def prepare_read_operation(self):
        self.assigned_textures = [TextureReadWrite(self.bytestream) for _ in range(self.texture_count)]

    def read(self):
        self.read_write(self.read_buffer, self.prepare_read_operation, "read")
        self.interpret_data()

    def read_write(self, rw_operator, preparation_op, rw_method_name):
        rw_operator("name_pointer", 'I', endianness='>')      
        rw_operator("unknown_0x04", 'I', endianness='>')       
        rw_operator("unknown_0x08", 'I', endianness='>')       
        rw_operator("padding_0x0A", 'I', endianness='>') 
        self.assert_is_zero("padding_0x0A")

        rw_operator("unknown_floats_1", 'f'*8, endianness='>')   
        rw_operator("texture_count", 'I', endianness='>')      
        rw_operator("texture_assignment_pointer", 'I', endianness='>')     
        rw_operator("unknown_floats_1", 'f'*43, endianness='>')
        
        
        if self.texture_assignment_pointer:
            self.assert_file_pointer_now_at(self.texture_assignment_pointer + self.offset)  
            rw_operator("texture_pointers", 'I'*self.texture_count, endianness='>', force_1d=True)
        
        preparation_op()
        for ptr, texture_reader in zip(self.texture_pointers, self.assigned_textures):
            self.assert_file_pointer_now_at(ptr + self.offset)
            getattr(texture_reader, rw_method_name)()
            
    def interpret_data(self):
        self.name = read_string_inplace(self.bytestream, self.name_pointer + self.offset)
        
texture_roles = {0: 'diffuse',
                 1: 'bumpmap',
                 4: 'specular',
                 5: 'reflective'}
        
class TextureReadWrite(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)
        self.padding_0x00 = None
        self.padding_0x04 = None
        self.role = None
        self.tex_idx = None
        
    def read(self):
        self.read_write(self.read_buffer)
        self.interpret_data()
        
    def read_write(self, rw_operator):
        rw_operator("padding_0x00", "I", endianness='>')
        rw_operator("padding_0x04", "I", endianness='>')
        rw_operator("role", "I", endianness='>')
        rw_operator("tex_idx", "I", endianness='>')
        self.assert_is_zero("padding_0x00")
        self.assert_is_zero("padding_0x04")
        
    def interpret_data(self):
        self.role = texture_roles[self.role]
        
def read_string_inplace(bytestream, pos):
    orig_pos = bytestream.tell()
    bytestream.seek(pos)
    res = read_string(bytestream)
    bytestream.seek(orig_pos)
    return res
    

def read_string(bytestream):
    b = None
    res = b''
    while b != b'\x00':
        b = bytestream.read(1)
        res += b
    return res[:-1].decode('ascii')


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]