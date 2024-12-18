import os
import subprocess
import shutil
from parse_idl import reproduce_idl_content, parse_idl_content
from generate_c_code import generate_c_code_for_method

class Generate():
    def __init__(self, idl_target_directory, cpp_target_directory, file_basename):
        super().__init__()
        self.idl_target_directory = idl_target_directory
        self.cpp_target_directory = cpp_target_directory
        self.file_basename = file_basename
        self.IDL_PATH = self.idl_target_directory + f"\\{self.file_basename}"
        self.CPP_PATH = self.cpp_target_directory + f"\\{self.file_basename}"
    
    def midl_compile(self):
        os.system(f"midl {self.IDL_PATH}.idl /out {self.idl_target_directory}")
        return os.path.isfile(f"{self.IDL_PATH}.h")

    def reproduce_idl(self):
        reproduce_idl_content(f'{self.IDL_PATH}.idl')
        
    def parse_idl(self):
        self.method_data, self.structless_methods, self.size_is_relationships = parse_idl_content(f'{self.IDL_PATH}.idl')
        print(self.method_data)
        return self.method_data
    
    def generate_c_code(self, method_name, need_handle_checked, null_dere_found):
        self.call_c_code, self.c_code = generate_c_code_for_method(method_name, self.method_data, self.size_is_relationships, need_handle_checked, null_dere_found)
        
    def generate_cpp(self, rpc_type, end_point, output):
        if output == '':
            files_to_delete = [f"{self.CPP_PATH}.cpp", f"{self.CPP_PATH}.exe"]
        else:
            output_path = self.cpp_target_directory + f"\\{output}"
            files_to_delete = [f"{self.CPP_PATH}.cpp", f"{output_path}.exe"]
            
        for file in files_to_delete:
            if os.path.isfile(file):
                os.remove(file)
                
        file_path = f"{self.CPP_PATH}.cpp"
        shutil.copy("tmp.cpp", file_path)
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        with open(file_path, "w", encoding="utf-8") as file:
            for i, line in enumerate(lines):
                file.write(line)
                if "Include Header" in line:
                    file.write(f'#include "{self.IDL_PATH}.h"\n')
                if "Rpc_Type" in line:
                    file.write(f'\t\t(RPC_WSTR)L"{rpc_type}",\n')
                if "End_Point" in line:
                    if end_point:
                        file.write(f'\t\t(RPC_WSTR)L"{end_point}",\n')
                    else:
                        file.write(f'\t\tNULL,\n')
                        
                if "Auto Generator - Call Client Code Start" in line:
                    file.write("\n" + self.call_c_code)
                    
                if "Auto Generator - Client Code Start" in line:
                    file.write("\n" + self.c_code)
                    
    def cpp_compile(self, output, dev_path):
        try:
            if dev_path != None:
                self.DEV_CMD = f'"{dev_path}" x64'
            else:
                self.DEV_CMD = r'"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" x64'
            if output == '':
                self.BUILD_CMD = f'cl /EHsc /O2 /MP /GL {self.CPP_PATH}.cpp {self.IDL_PATH}_c.c {self.IDL_PATH}_s.c /I . /link /LTCG /out:{self.CPP_PATH}.exe'
            else:
                output_path = self.cpp_target_directory + f"\\{output}"
                self.BUILD_CMD = f'cl /EHsc /O2 /MP /GL {self.CPP_PATH}.cpp {self.IDL_PATH}_c.c {self.IDL_PATH}_s.c /I . /link /LTCG /out:{output_path}.exe'
                
            process = subprocess.run(
                f'{self.DEV_CMD} && {self.BUILD_CMD}',
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )
            
            print("stdout:", process.stdout)
            print("stderr:", process.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print("명령 실행 중 오류 발생!")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            return False

    def clear_file(self):
        files_to_delete = [f"{self.IDL_PATH}.idl", f"{self.IDL_PATH}.h", f"{self.IDL_PATH}.obj", f"{self.IDL_PATH}_c.c", f"{self.IDL_PATH}_c.obj", f"{self.IDL_PATH}_s.c", f"{self.IDL_PATH}_s.obj", f"{self.file_basename}.obj", f"{self.file_basename}_c.obj", f"{self.file_basename}_s.obj"]

        for file in files_to_delete:
            if os.path.isfile(file):
                os.remove(file)

    def clear_file2(self):
        files_to_delete = [f"{self.file_basename}.obj", f"{self.file_basename}_c.obj", f"{self.file_basename}_s.obj"]

        for file in files_to_delete:
            if os.path.isfile(file):
                os.remove(file)