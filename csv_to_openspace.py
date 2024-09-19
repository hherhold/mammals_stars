#!/bin/env python

"""

# CSV to speck and labels

Each CSV file needs to be turned into a number of other files for OpenSpace.
First is the speck file, which contains the actual XYZ coordinates of the points,
drawn using RenderableStars. (Used to be RenderablePointCloud, but stars look
better.) We also need to create label files, which *are* RenderablePointClouds, except
without the actual points (though it does have point locations for the labels). These
turn into individual asset files. Each set of stars can have more than one set of labels.

Additionally, every CSV file has slightly different parameters as far as how it's
drawn by openspace. This info is all contained in the dataset csv file and these
parameters are used to create the speck and asset files. Some parameters affect
the speck file and some are renderable parameters and go in the asset file.

Labels are handled differently than stars, even though they're plotted at the same
locations as the stars. The labels are RenderablePointClouds that have no points, only
the locations of the labels. The label locations are in the CSV file, which must be
converted and copied to the OpenSpace asset dir as a label file. Additionally,
several different taxonomic levels and naming conventions may be used, which requires
different label files for each. Each line of the dataset CSV file determines
which column in the CSV file to use for generating labels. The 'type' column in the
dataset CSV file determines whether to make a stars or labels asset file.

"""

import argparse
import pandas as pd
from glob import glob
import shutil
import os
import math
from pathlib import Path

parser = argparse.ArgumentParser(description="Process input CSV files for OpenSpace.")
parser.add_argument("-i", "--input_dataset_csv_file", help="Input dataset CSV file.", 
                    required=True)
parser.add_argument("-c", "--cache_dir", help="OpenSpace cache directory.",
                    required=True)
parser.add_argument("-a", "--asset_dir", help="Output directory for assets.",
                    required=True)
parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")

def make_stars_speck_from_dataframe(input_points_df, filename_base,
                                    lum, absmag, colorb_v):

    output_speck_filename = filename_base + ".speck"

    with open(output_speck_filename, "w") as output_file:
        # Dump the speck file header info. 
        print("datavar 0 colorb_v", file=output_file)
        print("datavar 1 lum", file=output_file)
        print("datavar 2 absmag", file=output_file)
        print("datavar 3 appmag", file=output_file)
        print("datavar 4 texnum", file=output_file)
        print("datavar 5 distly", file=output_file)
        print("datavar 6 dcalc", file=output_file)
        print("datavar 7 plx", file=output_file)
        print("datavar 8 plxerr", file=output_file)
        print("datavar 9 vx", file=output_file)
        print("datavar 10 vy", file=output_file)
        print("datavar 11 vz", file=output_file)
        print("datavar 12 speed", file=output_file)
        print("texturevar 4", file=output_file)
        print("texture -M 1 halo.sgi", file=output_file)

        # Let's add columns for all the data we need to add to the speck file.
        input_points_df["colorb_v"] = colorb_v
        input_points_df["lum"] = lum
        input_points_df["absmag"] = absmag
        input_points_df["appmag"] = 0.0
        input_points_df["texnum"] = 0
        input_points_df["distly"] = 0.0
        input_points_df["dcalc"] = 0
        input_points_df["plx"] = 0.0
        input_points_df["plxerr"] = 0.0
        input_points_df["vx"] = 0
        input_points_df["vy"] = 0
        input_points_df["vz"] = 0
        input_points_df["speed"] = 0

        # For each row in the CSV file (pandas dataframe), we will write a line to the output file.
        for index, row in input_points_df.iterrows():
            # Split the line into a list of strings.
            datavars = []

            datavars.append(str(row["x"]))
            datavars.append(str(row["y"]))
            datavars.append(str(row["z"]))
            datavars.append(str(row["colorb_v"]))
            datavars.append(str(row["lum"]))
            datavars.append(str(row["absmag"]))
            datavars.append(str(row["appmag"]))
            datavars.append(str(row["texnum"]))
            datavars.append(str(row["distly"]))
            datavars.append(str(row["dcalc"]))
            datavars.append(str(row["plx"]))
            datavars.append(str(row["plxerr"]))
            datavars.append(str(row["vx"]))
            datavars.append(str(row["vy"]))
            datavars.append(str(row["vz"]))
            datavars.append(str(row["speed"]))

            # Write the modified line to the output file.
            output_file.write(" ".join(datavars) + "\n")

    # Return the name of the speck file we created.
    return([output_speck_filename])

def make_stars_asset_from_dataframe(input_points_df, 
                                    input_points_world_position,
                                    filename_base, 
                                    magnitude_exponent,
                                    core_multiplier,
                                    core_gamma,
                                    core_scale,
                                    glare_multiplier,
                                    glare_gamma,
                                    glare_scale,
                                    fade_target):

    output_filename = filename_base + ".asset"
    output_asset_position_name = filename_base + "_position"

    with open(output_filename, "w") as output_file:
        print("local sunspeck = asset.resource({", file=output_file)
        print("  Name = \"Stars Speck Files\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"digitaluniverse_sunstar_speck\",", file=output_file)
        print("  Version = 1", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)
        print("local colormaps = asset.resource({", file=output_file)
        print("  Name = \"Stars Color Table\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"stars_colormap\",", file=output_file)
        print("  Version = 3", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)
        print("local textures = asset.resource({", file=output_file)
        print("  Name = \"Stars Textures\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"stars_textures\",", file=output_file)
        print("  Version = 1", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)

        # "Declare" fade var so it can be used below.
        fade_varname = ""
        if fade_target:
            fade_varname = f"{filename_base}_fade_{fade_target}"

            print(f"local {fade_varname} = {{", file=output_file)
            print(f"    Identifier = \"{fade_varname}\",", file=output_file)
            print(f"    Name = \"{fade_varname}\",", file=output_file)
            print("    Command = [[", file=output_file)
            print("      openspace.printInfo(\"Node: \" .. args.Node)", file=output_file)
            print("      openspace.printInfo(\"Transition: \" .. args.Transition)", file=output_file)
            print("", file=output_file)
            print("      if args.Transition == \"Approaching\" then", file=output_file)
            print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target}.Renderable.Fade\", 0.0, 1.0)", file=output_file)
            print("      elseif args.Transition == \"Exiting\" then", file=output_file)
            print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target}.Renderable.Fade\", 1.0, 1.0)", file=output_file)
            print("      end", file=output_file)
            print("    ]],", file=output_file)
            print("    IsLocal = true", file=output_file)
            print("}", file=output_file)

        print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
        print(f"local {output_asset_position_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_position_name}\",", file=output_file)
        print("  Transform = {", file=output_file)
        print("    Translation = {", file=output_file)
        print("      Type = \"StaticTranslation\",", file=output_file)
        print("      Position = {", file=output_file)
        print(f"        {input_points_world_position["x"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["y"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["z"]} * meters_in_pc,", file=output_file)
        print("      }", file=output_file)
        print("     }", file=output_file)
        print("    },", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{output_asset_position_name}\",", file=output_file)
        print(f"    Path = \"/Positions\",", file=output_file)
        print(f"    Hidden = true", file=output_file)
        print("  }", file=output_file)
        print("}", file=output_file)

        print(f"local {filename_base}_speck = asset.resource(\"{filename_base}.speck\")", file=output_file)
        print("", file=output_file)
        print(f"local {filename_base} = {{", file=output_file)
        print(f"  Identifier = \"{filename_base}\",", file=output_file)
        print(f"  Parent = {output_asset_position_name}.Identifier,", file=output_file)
        print(f"  Renderable = {{", file=output_file)
        print("    UseCaching = false,", file=output_file)
        print("    Type = \"RenderableStars\",", file=output_file)
        print(f"    File = {filename_base}_speck,", file=output_file)
        print("    Core = {", file=output_file)
        print("      Texture = textures .. \"glare.png\",", file=output_file)
        print(f"      Multiplier = {core_multiplier},", file=output_file)
        print(f"      Gamma = {core_gamma},", file=output_file)
        print(f"      Scale = {core_scale}", file=output_file)
        print("    },", file=output_file)
        print("    Glare = {", file=output_file)
        print("      Texture = textures .. \"halo.png\",", file=output_file)
        print(f"      Multiplier = {glare_multiplier},", file=output_file)
        print(f"      Gamma = {glare_gamma},", file=output_file)
        print(f"      Scale = {glare_scale}", file=output_file)
        print("    },", file=output_file)
        print(f"    MagnitudeExponent = {magnitude_exponent},", file=output_file)
        print("    ColorMap = colormaps .. \"colorbv.cmap\",", file=output_file)
        print("    OtherDataColorMap = colormaps .. \"viridis.cmap\",", file=output_file)
        print("    SizeComposition = \"Distance Modulus\",", file=output_file)
        print("    DataMapping = {", file=output_file)
        print("      Bv = \"colorb_v\",", file=output_file)
        print("      Luminance = \"lum\",", file=output_file)
        print("      AbsoluteMagnitude = \"absmag\",", file=output_file)
        print("      ApparentMagnitude = \"appmag\",", file=output_file)
        print("      Vx = \"vx\",", file=output_file)
        print("      Vy = \"vy\",", file=output_file)
        print("      Vz = \"vz\",", file=output_file)
        print("      Speed = \"speed\"", file=output_file)
        print("    },", file=output_file)
        print("    DimInAtmosphere = true", file=output_file)
        print("  },", file=output_file)
        print("    InteractionSphere = 1 * meters_in_pc,", file=output_file)
        print("    ApproachFactor = 1000.0,", file=output_file)
        print("    ReachFactor = 5.0,", file=output_file)
        print("", file=output_file)
        if fade_target:
            print(f"    OnApproach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnReach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnRecede = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnExit = {{ \"{fade_varname}\" }},", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{filename_base}\",", file=output_file)
        print(f"    Path = \"/Stars\",", file=output_file)
        print("  }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        if fade_target:
            print(f"  openspace.action.registerAction({fade_varname})", file=output_file)
        print(f"  openspace.addSceneGraphNode({output_asset_position_name})", file=output_file)
        print(f"  openspace.addSceneGraphNode({filename_base})", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"  openspace.removeSceneGraphNode({filename_base})", file=output_file)
        print(f"  openspace.removeSceneGraphNode({output_asset_position_name})", file=output_file)
        if fade_target:
            print(f"  openspace.action.removeAction({fade_varname})", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_position_name})", file=output_file)
        print(f"asset.export({filename_base})", file=output_file)

    # Return the name of the asset file we created.
    return([output_filename])

def make_labels_from_dataframe(input_points_df, 
                               input_points_world_position,
                               filename_base,
                               label_column, label_size, label_minsize, label_maxsize, enabled):
    output_files = []

    label_filename = filename_base + "_" + label_column + ".label"
    with open(label_filename, "w") as output_file:
        for index, row in input_points_df.iterrows():
            print(f"{row['x']} {row['y']} {row['z']} id {index} text {row[label_column]}", file=output_file)

    output_files.append(label_filename)

    # Next the asset file for the label file. Same name as the label file, but with .asset
    # extension.
    output_asset_filename = filename_base + "_" + label_column + ".asset"
    output_asset_variable_name = filename_base + "_" + label_column + "_labels"
    output_asset_position_name = output_asset_variable_name + "_position"
    with open(output_asset_filename, "w") as output_file:
        print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
        print(f"local {output_asset_position_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_position_name}\",", file=output_file)
        print("  Transform = {", file=output_file)
        print("    Translation = {", file=output_file)
        print("      Type = \"StaticTranslation\",", file=output_file)
        print("      Position = {", file=output_file)
        print(f"        {input_points_world_position["x"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["y"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["z"]} * meters_in_pc,", file=output_file)
        print("      }", file=output_file)
        print("     }", file=output_file)
        print("    },", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{output_asset_position_name}\",", file=output_file)
        print(f"    Path = \"/Positions\",", file=output_file)
        print(f"    Hidden = true", file=output_file)
        print("  }", file=output_file)
        print(" }", file=output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = {output_asset_position_name}.Identifier,", file=output_file)
        print("    Renderable = {", file=output_file)
        print("        Type = \"RenderablePointCloud\",", file=output_file)
        print("        Labels = {", file=output_file)
        print(f"            File = asset.resource(\"{label_filename}\"),", file=output_file)
        print(f"            Enabled = {enabled},", file=output_file)
        print("            Unit = \"pc\",", file=output_file)
        print(f"            Size = {label_size},", file=output_file)
        print(f"            MinMaxSize = {{ {label_minsize},{label_maxsize} }}", file=output_file)
        print("        }", file=output_file)
        print("    },", file=output_file)
        print("    GUI = {", file=output_file)
        print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
        print(f"        Path = \"/Labels\"", file=output_file)
        print("    }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_position_name});", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_variable_name});", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_variable_name});", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_position_name});", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_position_name})", file=output_file)
        print(f"asset.export({output_asset_variable_name})", file=output_file)


    output_files.append(output_asset_filename)

    return(output_files)

def main():
    args = parser.parse_args()

    # Read the dataset CSV file into a pandas dataframe.
    input_dataset_df = pd.read_csv(args.input_dataset_csv_file, 
                                   comment="#")

    # A list of all the files created for this dataset. Each function below
    # returns the files it creates, so we can use this list to clean up the
    # cache directory.
    files_created = []

    # Now run the functions to create the speck and asset files for each csv
    # file in the dataset csv file.
    for index, row in input_dataset_df.iterrows():
        print("Reading file: " + row["csv_file"] + "... ", end="", flush=True)

        input_points_df = pd.read_csv(row["csv_file"])
        # The first column might be unnamed. It's basically the ID, so we'll
        # call it that for now.
        input_points_df.rename(columns={input_points_df.columns[0]: "ID"},
                                inplace=True)
        
        # The fade_target argument is optional. If it's blank, it's a NaN, which
        # is weird to test for if it might be a string. So convert it.
        fade_target = None
        if (str(row["fade_target"]) != "nan"):
            fade_target = row["fade_target"]

        # Let's get the base of the filename (no extension) to use for generating
        # output files.
        filename_base = row["csv_file"].replace(".csv", "")

        # All points are originally in world coordinates. A problem with this is we
        # need to be able to point the camera to certain locations, such as the center
        # of a set of points. To do this, we need to translate the points so that the
        # centroid of the points is locally at 0,0,0, and then move that whole set of
        # points to its original location using a transform.
        input_points_world_position = {}
        input_points_world_position["x"] = input_points_df["x"].mean()
        input_points_world_position["y"] = input_points_df["y"].mean()
        input_points_world_position["z"] = input_points_df["z"].mean()
        #print("Centroid (world position of center of points): ", input_points_world_position)

        # Translate all the points so that the new centroid of the points is 0,0,0.
        input_points_df["x"] = input_points_df["x"] - input_points_world_position["x"]
        input_points_df["y"] = input_points_df["y"] - input_points_world_position["y"]
        input_points_df["z"] = input_points_df["z"] - input_points_world_position["z"]

        if row["type"] == "labels":
            print("Creating labels... ", end="", flush=True)
            # Let's do the labels first. The following functions modify the original
            # dataframe, adding lots of columns for the speck file, but making labels
            # doesn't. So we can do this first.
            # "enabled" is wonky. It is 1 or 0 in the CSV file, we need to change
            # it to true or false.
            if row["enabled"] == 1:
                row["enabled"] = "true"
            else:
                row["enabled"] = "false"
            files_created += \
                make_labels_from_dataframe(input_points_df=input_points_df,
                                           input_points_world_position=input_points_world_position,
                                           filename_base=filename_base,
                                           label_column=row["label_column"],
                                           label_size=row["label_size"],
                                           label_minsize=row["label_minsize"],
                                           label_maxsize=row["label_maxsize"],
                                           enabled=row["enabled"])

        elif row["type"] == "stars":
            print("Creating stars... ", end="", flush=True)
            # Now the speck file. This is what RenderableStars will use to draw the
            # points. The speck file doesn't care about the centroid; the translation
            # to "world" space is applied by the renderable.
            files_created += \
                make_stars_speck_from_dataframe(input_points_df=input_points_df, 
                                                filename_base=filename_base,
                                                lum=row["lum"], 
                                                absmag=row["absmag"],
                                                colorb_v=row["colorb_v"])

            # Now an asset file that will be used to load the speck file into OpenSpace.
            files_created += \
                make_stars_asset_from_dataframe(input_points_df=input_points_df, 
                                                input_points_world_position=input_points_world_position,
                                                filename_base=filename_base,
                                                magnitude_exponent=row["MagnitudeExponent"],
                                                core_multiplier=row["core_multiplier"],
                                                core_gamma=row["core_gamma"],
                                                core_scale=row["core_scale"],
                                                glare_multiplier=row["glare_multiplier"],
                                                glare_gamma=row["glare_gamma"],
                                                glare_scale=row["glare_scale"],
                                                fade_target=fade_target)
        print("Done.")


    # Now we need to make a list of all the .asset and .speck files we created
    # so these can be flushed from the cache directory.
    print("Cleaning cache directory...", end="", flush=True)
    for file in files_created:
        # Ignore any errors if the file doesn't exist.
        try:
            if args.verbose:
                print(f"Removing {args.cache_dir + '/' + file}")
            os.remove(args.cache_dir + "/" + file)
        except:
            pass
    print("Done.")
    
    # Now copy the speck and asset files to the output directory.
    print(f"Copying files to output directory ({args.asset_dir}).")
    Path(args.asset_dir).mkdir(parents=True, exist_ok=True)
    for file in files_created:
        if args.verbose:
            print(f"{file} ", end="", flush=True)
        shutil.copy2(file, args.asset_dir)
    print("Done.")

if __name__ == '__main__':
    main()
    