# AllStarRumbleModelTool
A program to convert PXBI files to COLLADA.

Intended to be used with `.bin` files from "Digimon All-Star Rumble".
This program is unlikely to be actively worked on, but pull requests that add useful code fixes and functionality are very welcome and should receive attention.

## Dependencies
- Python >= 3.6

## Usage
The tool can be passed either a `.bin` file or a folder containing `.bin` files. In the first instance, the model will be extracted to a folder with the same name as the input `.bin` file. If it is given a folder, each file will be extracted to a folder with the same name as the input `.bin` file inside a folder "out".

If you have downloaded a release, you can **drag-and-drop these files and folders onto the executable**.

The tool can also be called from Python:
```
python PXBItoCollada.py <file>
python PXBItoCollada.py <folder>
```

Or if you have downloaded a release, from the command-line with the executable:
```
PXBItoCollada.exe <file>
PXBItoCollada.exe <folder>
```

## Known Issues
- Uncompressed textures do not export well. The tool also exports the raw GTF files, such that alternative GTF conversion tools can be used to convert these files.
- Some textures have bad alpha-channel data that must be manually fixed in an external program.
- The skeletons _may_ not be exactly correct.
- Materials do not export with any information other than textures; information such as specular coefficients have not been pinpointed within the material data structures in the files and are therefore not extracted.
- Vertex tangents and binormals may be the wrong way around, needs confirmation.

## Acknowledgements
Thanks to [alicebitland](https://www.deviantart.com/alicebitland) and [WarGrey-Sama](https://www.deviantart.com/wargrey-sama). Additional thanks to WarGrey-Sama for requesting that these tools be built, assistance with the texture format, as well as sharing tools and expertise. Exports with fixes to models and textures that export with issues are available on WarGrey-Sama's [DeviantArt profile](https://www.deviantart.com/wargrey-sama).

Thanks to [SydMontague](https://github.com/SydMontague) for help fixing vertex weight issues in the COLLADA exporter!

Releases are compiled with [PyInstaller 4.3 for Python 3.9.4](https://www.pyinstaller.org/).

Utilises code from [this repository for matrix inverses](https://github.com/ThomIves/MatrixInverse) to remove the NumPy dependency.
