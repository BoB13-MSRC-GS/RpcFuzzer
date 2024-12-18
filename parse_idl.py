import re
from collections import defaultdict

def reproduce_idl_content(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    flag = False
    with open(file_path, "w", encoding="utf-8") as file:
        for i, line in enumerate(lines):
            if flag:
                if 'arg' in line:
                    file.write(", \n")
                else:
                    file.write("\n")
                flag = False
            file.write(line)
            if " Proc" in line:
                file.write(f'	[in]handle_t hBinding')
                flag = True

def parse_idl_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    method_pattern = re.compile(r'(?:\w+)\s+(Proc\d+)(?:_(\w+))?\s*\((.*?)\);', re.DOTALL)
    methods = method_pattern.findall(content)

    method_data = []
    structless_methods = []
    size_is_relationships = defaultdict(list)

    struct_pattern = re.compile(r'\bstruct\b')

    for proc_name, suffix, params in methods:
        method_name = f"{proc_name}_{suffix}" if suffix else proc_name

        param_list = [param.strip() for param in params.split(', ') if param.strip()]
        param_info = []
        has_struct = False

        for param in param_list:
            param2 = re.sub(r'/\*.*?\*/', '', param)
            
            if "hBinding" in param2:
                continue
            size_is_match = re.search(r'\bsize_is\((.*?)\)', param2)
            
            param_match = param2.split("]")[-1]
            find = True
            if "arg" in param_match:
                data = param_match.split("arg")
                data[0] = data[0].replace("[unique]", "")
                data[0] = data[0].replace("[string]", "")
                data[0] = data[0].replace("[ref]", "")
                data[0] = data[0].replace("[ptr]", "")
                data[0] = data[0].replace("[context_handle]", "")
                base_type = data[0].strip()
                
                param_name = "arg" + data[1]
            else:
                find = False

            if find:
                if "[out]" in param2:
                    param_info.append((base_type, param_name, 'out'))
                else:
                    param_info.append((base_type, param_name, 'in'))

                if struct_pattern.search(base_type):
                    has_struct = True

                if size_is_match:
                    size_is_target = size_is_match.group(1)
                    if '/' in size_is_target:
                        size_is_target = size_is_target.split('/')[0]
                        size_is_target.strip()
                    if 'arg' in size_is_target:
                        size_is_relationships[method_name].append((param_name, size_is_target))

        method_data.append({
            'method_name': method_name,
            'param_count': len(param_list),
            'param_info': param_info,
            'has_struct': has_struct
        })

        if not has_struct:
            structless_methods.append(method_name)

    return method_data, structless_methods, size_is_relationships