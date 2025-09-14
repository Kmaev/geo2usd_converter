
# Geo to USD CLI tool:

Demo: https://vimeo.com/1097411468

A CLI tool that converts geometry files (e.g., .bgeo.sc, .fbx) into .usd format.
It parses textures based on a library name (currently supported: Kitbash, Megascans) or from a specified texture folder, creates MaterialX shaders populated with the corresponding textures, and automatically binds materials to USD primitives.

Requirements

USD must be installed in your environment.

A valid Houdini license is required to run the conversion (uses hython).

Usage

Run the following command:

hython /path/to/hython \
    /path/to/convert_to_usd.py \
    --asset-lib-path /path/to/your/geometry \
    --lib-name Kitbash \
    --textures-folder-path /path/to/textures
    

Arguments
- `--asset-lib-path (required): Path to the geometry file or asset directory.
- `--lib-name (optional): Name of the texture library (e.g., Kitbash, Megascans).
- `--textures-folder-path (optional): Path to the texture folder, if not using library name.
If neither --lib-name nor --textures-folder-path is provided, the tool defaults to using the geometry folder as the texture source.

Folder Structure Requirement

If you specify a library name, ensure the folder structure matches the original layout from the corresponding marketplace (e.g., Kitbash or Megascans).


Example usage (Kitbash):

<img width="926" alt="image" src="https://github.com/user-attachments/assets/645daef6-134b-43ff-b262-5ba94e3d5bfa" />

Example usage (Megascans):

<img width="926" alt="image" src="https://github.com/user-attachments/assets/35909173-ec2f-415c-9f79-787611258b66" />

Note: In the case of Megascans, each asset must be stored in a separate folder alongside its corresponding textures, following the folder structure shown in the image below:

<img width="768" alt="image" src="https://github.com/user-attachments/assets/6950747b-8042-4af6-a051-1f8712ae8d88" />

Example: Kitbash default folder structure

<img width="768" alt="image" src="https://github.com/user-attachments/assets/1369e52a-7921-4e6f-a0d2-80a999bde188" />


Example usage: 

Match geometry and texture folders independently of the library:

<img width="926" alt="image" src="https://github.com/user-attachments/assets/2ceddd47-8d63-42ae-a063-da2b38b11567" />

To properly resolve textures, their names should be similar to the names of the primitives you're binding them to.
This method relies on clean naming and structure — so keeping things organized is key 😉



