def format_code_with_indentation(code, indent_level):
    formatted_code = []

    for line in code.splitlines():
        stripped_line = line.rstrip()

        if stripped_line.startswith("}") or stripped_line.endswith("}}}}"):
            indent_level -= 1

        formatted_code.append("    " * indent_level + stripped_line)

        if stripped_line.endswith("{") and not stripped_line.startswith("}"):
            indent_level += 1

    return "\n".join(formatted_code)

def generate_c_code_for_method(method_name, method_data, size_is_relationships, need_handle_checked, null_dere_found):
    method = next((m for m in method_data if m['method_name'] == method_name), None)
    if not method:
        print(f"Method {method_name} not found.")
        return None

    size_is_info = size_is_relationships.get(method_name, [])
    param_info = method['param_info']

    setup_code = []
    cleanup_code = []
    func_call_params = ["hBinding"]
    func_call_real_params = ["hBinding"]
    loop_code = []

    fixed_params = {target for _, target in size_is_info}

    for base_type, param_name, direction in param_info:
        clean_type = base_type.replace("const", "").strip()
        pointer_depth = clean_type.count('*')
        base_type = clean_type.replace("*", "").strip()
        if 'wchar' not in base_type:
            base_type = base_type.replace("char", "unsigned char")
        
        if direction == "in":
            size_is_target = next((target for param, target in size_is_info if param == param_name), None)

            if size_is_target:
                size_is_target_cleaned = size_is_target.replace("*", "").strip()
                size_is_base_type = next((base_type for base_type, param_name, direction in param_info if param_name == size_is_target_cleaned), None)
                if null_dere_found:
                    setup_code.append(f"{size_is_base_type} {size_is_target_cleaned} = 0;")
                else:
                    setup_code.append(f"{size_is_base_type} {size_is_target_cleaned} = 0x1000;")
            
                setup_code.append(f"{base_type} {'*' * pointer_depth}{param_name} = ({base_type} {'*' * pointer_depth})malloc({size_is_target} * sizeof({base_type}{ ('*' * (pointer_depth - 1))}));")
                setup_code.append(f"memset({param_name}, 0, {size_is_target} * sizeof({base_type}{ ('*' * (pointer_depth - 1))}));")
                
                cleanup_code.append(f"free({param_name});")
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
                continue

            if param_name in fixed_params or '*'+param_name in fixed_params or '**'+param_name in fixed_params:
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
                continue
                
            if pointer_depth == 0:
                if base_type in {"hyper", "long", "unsigned __int3264"}:
                    loop_code.append(f"for (unsigned int {param_name} : list_4byte) {{")
                elif base_type in {"short", "small"}:
                    loop_code.append(f"for (unsigned short {param_name} : list_2byte) {{")
                elif base_type in {"unsigned char", "char", "byte"}:
                    loop_code.append(f"for (unsigned char {param_name} : list_1byte) {{")
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
                continue
            elif pointer_depth == 1:
                if 'void' in base_type:
                    if need_handle_checked:
                        func_call_params.append("chandle")
                        func_call_real_params.append(param_name)
                    else:
                        setup_code.append(f"INT64 test = 0;")
                        setup_code.append(f"{base_type} *{param_name} = &test;")
                        func_call_params.append(param_name)
                        func_call_real_params.append(param_name)
                else:
                    setup_code.append(f"{base_type} *{param_name} = ({base_type} *)malloc(0x1000 * sizeof({base_type}));")
                    cleanup_code.append(f"free({param_name});")
                    func_call_params.append(param_name)
                    func_call_real_params.append(param_name)
            elif pointer_depth == 2:
                setup_code.append(f"{base_type} **{param_name} = ({base_type} **)malloc(0x1000 * sizeof({base_type} *));")
                cleanup_code.append(f"free({param_name});")
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
            else:
                setup_code.append(f"{base_type} {param_name} = 0;")
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)

        elif direction == "out":
            size_is_target = next((target for param, target in size_is_info if param == param_name), None)

            if size_is_target:
                size_is_target_cleaned = size_is_target.replace("*", "").strip()
                size_is_base_type = next((base_type for base_type, param_name, direction in param_info if param_name == size_is_target_cleaned), None)
                size_is_base_type_cleaned = size_is_base_type.replace("*", "").strip()
                size_is_base_type_pointer_depth = size_is_base_type.count('*')
                if size_is_base_type_pointer_depth == 0:
                    setup_code.append(f"{size_is_base_type} {size_is_target_cleaned} = 0x10;")
                else:
                    setup_code.append(f"{size_is_base_type} {size_is_target_cleaned} = ({size_is_base_type})malloc(sizeof({size_is_base_type_cleaned}));")
                    setup_code.append(f"*{size_is_target_cleaned} = 0x10;")
                    cleanup_code.append(f"free({size_is_target_cleaned});")

                if pointer_depth == 1:
                    setup_code.append(f"{base_type} *{param_name} = ({base_type} *)malloc({size_is_target} * sizeof({base_type}));")
                    cleanup_code.append(f"free({param_name});")
                    func_call_params.append(param_name)
                else:
                    setup_code.append(f"{base_type} {'*' * (pointer_depth - 1)}{param_name} = ({base_type} {'*' * (pointer_depth - 1)})malloc({size_is_target} * sizeof({base_type}{ ('*' * (pointer_depth - 2))}));")
                    cleanup_code.append(f"free({param_name});")
                    func_call_params.append(f"&{param_name}")
                func_call_real_params.append(param_name)
                continue
            
            if param_name in fixed_params or '*'+param_name in fixed_params or '**'+param_name in fixed_params:
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
                continue
            
            if pointer_depth == 1:
                if 'struct' in base_type:
                    setup_code.append(f"{base_type} *{param_name} = new {base_type.split(' ')[1]};")
                    func_call_params.append(param_name)
                    func_call_real_params.append(param_name)
                else:
                    setup_code.append(f"{base_type} {param_name} = 0;")
                    func_call_params.append(f"&{param_name}")
                    func_call_real_params.append(param_name)
            elif pointer_depth == 2:
                if 'void' in base_type:
                    setup_code.append(f"INT64 test = 0;")
                    setup_code.append(f"{base_type} *{param_name} = &test;")
                    func_call_params.append(f"&{param_name}")
                    func_call_real_params.append(param_name)
                else:
                    setup_code.append(f"{base_type} *{param_name} = nullptr;")
                    func_call_params.append(f"&{param_name}")
                    func_call_real_params.append(param_name)
            elif pointer_depth == 3:
                setup_code.append(f"{base_type} **{param_name} = nullptr;")
                func_call_params.append(f"&{param_name}")
                func_call_real_params.append(param_name)
            else:
                setup_code.append(f"{base_type} {param_name} = 0;")
                func_call_params.append(param_name)
                func_call_real_params.append(param_name)
    
    func_call = f"Call{method_name}({', '.join(func_call_params)});\n"
        
    c_code = loop_code + setup_code + [func_call] + cleanup_code
    if need_handle_checked:
        with open("get_handle.cpp", "r", encoding="utf-8") as file:
            lines = file.read()
        # print(lines)
        c_code = [lines] + loop_code + setup_code + [func_call] + cleanup_code
        
    c_code.append("}\n" * len(loop_code))
    c_code.append("// Auto Generator - Client Code Finish")
    formatted_c_code = format_code_with_indentation("\n".join(c_code), 1)
    
    
    func_call = []
    func_call.append(f"void Call{method_name}(")
    if len(param_info):
        func_call.append(f"    RPC_BINDING_HANDLE hBinding,")
    else:
        func_call.append(f"    RPC_BINDING_HANDLE hBinding")
        
    for base_type, param_name, direction in param_info:
        clean_type = base_type.replace("const", "").strip()
        if 'wchar' not in clean_type:
            clean_type = clean_type.replace("char", "unsigned char")
        func_call.append(f"    {clean_type} {param_name},")
    tmp = func_call.pop()
    tmp = tmp.replace(',', '')
    func_call.append(tmp)
    func_call.append(f") {{")
    func_call.append(f"__try {{")
    func_call.append(f"{method_name}({', '.join(func_call_real_params)});")
    func_call.append('}\n__except (EXCEPTION_EXECUTE_HANDLER) {\nprintf("[-] Error : 0x%08X\\n", RpcExceptionCode());')
    func_call.append(f"}}")
    func_call.append(f"}}")
    func_call.append("\n// Auto Generator - Call Client Code Finish")
    
    formatted_call_c_code = format_code_with_indentation("\n".join(func_call), 0)
        
    return formatted_call_c_code, formatted_c_code