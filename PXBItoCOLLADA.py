import os
import sys

from ColladaConvert import PXBItoCollada

if __name__ == "__main__":
    if len(sys.argv) == 0:
        print("Insufficient input parameters.")
        print("Usage: ")
        print("    PXBItoCollada.exe <folder>")
        print("    PXBItoCollada.exe <file>")
    else:
        input_arg = sys.argv[1]
        if os.path.isdir(input_arg):
            for file in os.listdir(input_arg):
                if os.path.splitext(file)[-1] != '.bin':
                    continue
                print(f"Converting {file}...")
                filepath = os.path.join(input_arg, file)
                output_dir = os.path.join("out", os.path.splitext(file)[0])
                os.makedirs(output_dir, exist_ok=True)
                try:
                    PXBItoCollada(filepath, output_dir)
                except Exception as e:
                    print(f"Conversion failed with the following error: {e}")
        elif os.path.isfile(input_arg):
            output_dir = os.path.splitext(input_arg)[0]
            os.makedirs(output_dir, exist_ok=True)
            PXBItoCollada(input_arg, output_dir)
        else:
            print(f"'{input_arg}' was not recognised as a file or directory.")
