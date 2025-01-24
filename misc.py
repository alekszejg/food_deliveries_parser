def print_exception_info(func_name, e_name="Unexpected Error", reason="", e=""):
    output = f"\n!!! {e_name} caught in {func_name}() !!!\n"
    
    if reason:
        output += f" Possible reason: {reason}\n"
    if e:
        output += f" {e}\n"   
    
    print(output)