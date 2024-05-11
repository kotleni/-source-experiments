//Maya ASCII 7.0 scene
//Name: combinationCube.ma
//Last modified: Mon, Dec 03, 2007 07:48:23 PM
requires maya "7.0";
currentUnit -l centimeter -a degree -t ntsc;
fileInfo "application" "maya";
fileInfo "product" "Maya Complete 7.0";
fileInfo "version" "7.0.1";
fileInfo "cutIdentifier" "200511200915-660870";
fileInfo "osv" "Microsoft Windows XP Service Pack 2 (Build 2600)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 5.1932057041116311 87.46461290823251 67.896934227925883 ;
	setAttr ".r" -type "double3" -45.938352729604112 0.99999999999969313 1.491112110532821e-016 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".fcp" 10000;
	setAttr ".coi" 116.71229717856428;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 7.0330282688798178 7.2096947325316982 -17.399606545124541 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 100.1 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".fcp" 10000;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 20.25360653030134 21.596794605255127 103.21408106692284 ;
createNode camera -s -n "frontShape" -p "front";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".fcp" 10000;
	setAttr ".coi" 100.1;
	setAttr ".ow" 432.77951779300577;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 100.1 0 0 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".fcp" 10000;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "base";
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "baseShape" -p "base";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode mesh -n "baseShapeOrig" -p "base";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".vt[0:7]"  -3.75 1.3182769 3.75 3.75 1.3182769 3.75 
		-3.75 8.8182774 3.75 3.75 8.8182774 3.75 -3.75 8.8182774 -3.75 3.75 8.8182774 -3.75 
		-3.75 1.3182769 -3.75 3.75 1.3182769 -3.75;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "uncorrected";
	setAttr ".rp" -type "double3" -89.264842807747925 0 -78.191151413125993 ;
	setAttr ".sp" -type "double3" -89.264842807747925 0 -78.191151413125993 ;
createNode transform -n "a" -p "uncorrected";
	setAttr ".t" -type "double3" -38.821903739473385 8.8817841970012523e-016 -15.016753002480456 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "aShape" -p "a";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.7499905 -5.6371007 -8.7499971 
		-8.7499943 -5.6371007 -8.7499971 8.7499905 -18.854269 -8.7499971 -8.7499943 -18.854269 
		-8.7499971 8.7499905 -18.854269 8.7499952 -8.7499943 -18.854269 8.7499952 8.7499905 
		-5.6371007 8.7499952 -8.7499943 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "b" -p "uncorrected";
	setAttr ".t" -type "double3" -28.773898839747972 8.8817841970012523e-016 -15.016753002480456 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "bShape" -p "b";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.7500057 -5.6371007 -8.7499971 
		-6.2377572 -5.6371007 -8.7499971 8.7500057 -23.1371 -8.7499971 -6.2377572 -23.1371 
		-8.7499971 8.7500057 -23.1371 8.7499952 -6.2377572 -23.1371 8.7499952 8.7500057 -5.6371007 
		8.7499952 -6.2377572 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "relativeCorrectors";
	setAttr ".rp" -type "double3" 0 0 -78.191151413125993 ;
	setAttr ".sp" -type "double3" 0 0 -78.191151413125993 ;
createNode transform -n "aRelative" -p "relativeCorrectors";
	setAttr ".t" -type "double3" -10.856717054081926 8.8817841970012523e-016 -15.016753002480456 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "aRelativeShape" -p "aRelative";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.750001 -5.6371007 -8.7499971 
		-8.749999 -5.6371007 -8.7499971 8.750001 -18.854269 -8.7499971 -8.749999 -18.854269 
		-8.7499971 8.750001 -18.854269 8.7499952 -8.749999 -18.854269 8.7499952 8.750001 
		-5.6371007 8.7499952 -8.749999 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "bRelative" -p "relativeCorrectors";
	setAttr ".t" -type "double3" 0 0 -15.016753002480471 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "bRelativeShape" -p "bRelative";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.750001 -5.6371007 -8.7499971 
		-6.2377534 -5.6371007 -8.7499971 8.750001 -23.1371 -8.7499971 -6.2377534 -23.1371 
		-8.7499971 8.750001 -23.1371 8.7499952 -6.2377534 -23.1371 8.7499952 8.750001 -5.6371007 
		8.7499952 -6.2377534 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "aRelative_bRelative" -p "relativeCorrectors";
	setAttr ".t" -type "double3" 12.52546295027102 0 -15.016753002480471 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "aRelative_bRelativeShape" -p "aRelative_bRelative";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.750001 -5.6371007 -8.7499971 
		-8.749999 -5.6371007 -8.7499971 8.750001 -23.1371 -8.7499971 -11.088408 -25.475513 
		-8.7499971 8.750001 -23.1371 8.7499952 -11.088408 -25.475513 8.7499952 8.750001 -5.6371007 
		8.7499952 -8.749999 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "absoluteCorrectors";
	setAttr ".rp" -type "double3" 116.03996715239879 0 -78.191151413125993 ;
	setAttr ".sp" -type "double3" 116.03996715239879 0 -78.191151413125993 ;
createNode transform -n "aAbsolute" -p "absoluteCorrectors";
	setAttr ".t" -type "double3" 30.064724505970148 0 -15.016753002480471 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "aAbsoluteShape" -p "aAbsolute";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.7500019 -5.6371007 -8.7499971 
		-8.7499981 -5.6371007 -8.7499971 8.7500019 -18.854269 -8.7499971 -8.7499981 -18.854269 
		-8.7499971 8.7500019 -18.854269 8.7499952 -8.7499981 -18.854269 8.7499952 8.7500019 
		-5.6371007 8.7499952 -8.7499981 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "bAbsolute" -p "absoluteCorrectors";
	setAttr ".t" -type "double3" 40.489619162855178 0 -15.016753002480471 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "bAbsoluteShape" -p "bAbsolute";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.7500019 -5.6371007 -8.7499971 
		-6.2377529 -5.6371007 -8.7499971 8.7500019 -23.1371 -8.7499971 -6.2377529 -23.1371 
		-8.7499971 8.7500019 -23.1371 8.7499952 -6.2377529 -23.1371 8.7499952 8.7500019 -5.6371007 
		8.7499952 -6.2377529 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode transform -n "aAbsolute_bAbsolute" -p "absoluteCorrectors";
	setAttr ".t" -type "double3" 53.332834336797646 0 -15.016753002480471 ;
	setAttr ".rp" -type "double3" 0 5.0682767993368891 0 ;
	setAttr ".sp" -type "double3" 0 5.0682767993368891 0 ;
createNode mesh -n "aAbsolute_bAbsoluteShape" -p "aAbsolute_bAbsolute";
	setAttr -k off ".v";
	setAttr -s 2 ".iog[0].og";
	setAttr ".iog[0].og[8].gcl" -type "componentList" 1 "vtx[*]";
	setAttr ".iog[0].og[9].gcl" -type "componentList" 1 "vtx[*]";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".pt[0:7]" -type "float3"  8.75 -5.6371007 -8.7499971 
		-6.2377491 -5.6371007 -8.7499971 8.75 -18.854265 -8.7499971 -8.5761662 -21.19268 
		-8.7499971 8.75 -18.854265 8.7499952 -8.5761662 -21.19268 8.7499952 8.75 -5.6371007 
		8.7499952 -6.2377491 -5.6371007 8.7499952;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode mesh -n "aAbsolute_bAbsoluteShape1Orig" -p "aAbsolute_bAbsolute";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0 0 1 0 0 1 1 1 
		0 2 1 2 0 3 1 3 0 4 1 4 2 0 2 1 -1 0 -1 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".vt[0:7]"  -12.5 6.9553776 12.5 12.5 6.9553776 12.5 
		-12.5 31.955378 12.5 12.5 31.955378 12.5 -12.5 31.955378 -12.5 12.5 31.955378 -12.5 
		-12.5 6.9553776 -12.5 12.5 6.9553776 -12.5;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		4 5 0 6 7 0 0 2 0 1 3 0 
		2 4 0 3 5 0 4 6 0 5 7 0 
		6 0 0 7 1 0;
	setAttr -s 6 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5 
		mu 0 4 0 1 3 2 
		f 4 1 7 -3 -7 
		mu 0 4 2 3 5 4 
		f 4 2 9 -4 -9 
		mu 0 4 4 5 7 6 
		f 4 3 11 -1 -11 
		mu 0 4 6 7 9 8 
		f 4 -12 -10 -8 -6 
		mu 0 4 1 10 11 3 
		f 4 10 4 6 8 
		mu 0 4 12 0 2 13 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
createNode lightLinker -n "lightLinker1";
	setAttr -s 4 ".lnk";
createNode displayLayerManager -n "layerManager";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 0 -max 30 -ast 0 -aet 30 ";
	setAttr ".st" 6;
createNode lambert -n "relativeCorrectors_mat";
	setAttr ".c" -type "float3" 0.5 0.06139832 0.014999986 ;
createNode shadingEngine -n "relativeCorrectorsSG";
	setAttr ".ihi" 0;
	setAttr -s 3 ".dsm";
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo1";
createNode lambert -n "absoluteCorrectors_mat";
	setAttr ".c" -type "float3" 0 0.35666668 0.5 ;
createNode shadingEngine -n "absoluteCorrectorsSG";
	setAttr ".ihi" 0;
	setAttr -s 3 ".dsm";
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo2";
createNode blendShape -n "blendShape1";
	addAttr -ci true -h true -sn "aal" -ln "attributeAliasList" -bt "ATAL" -dt "attributeAlias";
	setAttr -s 8 ".w[0:7]"  0 0 0 0 0 0 0 0;
	setAttr -s 8 ".it[0].itg";
	setAttr ".aal" -type "attributeAlias" {"a","weight[0]","b","weight[1]","aRelative"
		,"weight[2]","bRelative","weight[3]","aRelative_bRelative","weight[4]","aAbsolute"
		,"weight[5]","bAbsolute","weight[6]","aAbsolute_bAbsolute","weight[7]"} ;
createNode tweak -n "tweak1";
createNode objectSet -n "blendShape1Set";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "blendShape1GroupId";
	setAttr ".ihi" 0;
createNode groupParts -n "blendShape1GroupParts";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode objectSet -n "tweakSet1";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId2";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts2";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
select -ne :time1;
	setAttr ".o" 0;
select -ne :renderPartition;
	setAttr -s 4 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 4 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :lightList1;
select -ne :initialShadingGroup;
	setAttr -k on ".cch";
	setAttr -k on ".nds";
	setAttr -s 3 ".dsm";
	setAttr -k on ".mwc";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr -k on ".cch";
	setAttr -k on ".nds";
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	setAttr ".fs" 1;
	setAttr ".ef" 10;
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :defaultHardwareRenderGlobals;
	setAttr -l on ".ef";
	setAttr -l on ".bf";
	setAttr -l on ".sf";
	setAttr ".fn" -type "string" "im";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
connectAttr "blendShape1GroupId.id" "baseShape.iog.og[23].gid";
connectAttr "blendShape1Set.mwc" "baseShape.iog.og[23].gco";
connectAttr "groupId2.id" "baseShape.iog.og[24].gid";
connectAttr "tweakSet1.mwc" "baseShape.iog.og[24].gco";
connectAttr "blendShape1.og[0]" "baseShape.i";
connectAttr "tweak1.vl[0].vt[0]" "baseShape.twl";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[2].llnk";
connectAttr "relativeCorrectorsSG.msg" "lightLinker1.lnk[2].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[3].llnk";
connectAttr "absoluteCorrectorsSG.msg" "lightLinker1.lnk[3].olnk";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "relativeCorrectors_mat.oc" "relativeCorrectorsSG.ss";
connectAttr "aRelative_bRelativeShape.iog" "relativeCorrectorsSG.dsm" -na;
connectAttr "bRelativeShape.iog" "relativeCorrectorsSG.dsm" -na;
connectAttr "aRelativeShape.iog" "relativeCorrectorsSG.dsm" -na;
connectAttr "relativeCorrectorsSG.msg" "materialInfo1.sg";
connectAttr "relativeCorrectors_mat.msg" "materialInfo1.m";
connectAttr "absoluteCorrectors_mat.oc" "absoluteCorrectorsSG.ss";
connectAttr "aAbsolute_bAbsoluteShape.iog" "absoluteCorrectorsSG.dsm" -na;
connectAttr "bAbsoluteShape.iog" "absoluteCorrectorsSG.dsm" -na;
connectAttr "aAbsoluteShape.iog" "absoluteCorrectorsSG.dsm" -na;
connectAttr "absoluteCorrectorsSG.msg" "materialInfo2.sg";
connectAttr "absoluteCorrectors_mat.msg" "materialInfo2.m";
connectAttr "blendShape1GroupParts.og" "blendShape1.ip[0].ig";
connectAttr "blendShape1GroupId.id" "blendShape1.ip[0].gi";
connectAttr "aShape.w" "blendShape1.it[0].itg[0].iti[6000].igt";
connectAttr "bShape.w" "blendShape1.it[0].itg[1].iti[6000].igt";
connectAttr "aRelativeShape.w" "blendShape1.it[0].itg[2].iti[6000].igt";
connectAttr "bRelativeShape.w" "blendShape1.it[0].itg[3].iti[6000].igt";
connectAttr "aRelative_bRelativeShape.w" "blendShape1.it[0].itg[4].iti[6000].igt"
		;
connectAttr "aAbsoluteShape.w" "blendShape1.it[0].itg[5].iti[6000].igt";
connectAttr "bAbsoluteShape.w" "blendShape1.it[0].itg[6].iti[6000].igt";
connectAttr "aAbsolute_bAbsoluteShape.w" "blendShape1.it[0].itg[7].iti[6000].igt"
		;
connectAttr "groupParts2.og" "tweak1.ip[0].ig";
connectAttr "groupId2.id" "tweak1.ip[0].gi";
connectAttr "blendShape1GroupId.msg" "blendShape1Set.gn" -na;
connectAttr "baseShape.iog.og[23]" "blendShape1Set.dsm" -na;
connectAttr "blendShape1.msg" "blendShape1Set.ub[0]";
connectAttr "tweak1.og[0]" "blendShape1GroupParts.ig";
connectAttr "blendShape1GroupId.id" "blendShape1GroupParts.gi";
connectAttr "groupId2.msg" "tweakSet1.gn" -na;
connectAttr "baseShape.iog.og[24]" "tweakSet1.dsm" -na;
connectAttr "tweak1.msg" "tweakSet1.ub[0]";
connectAttr "baseShapeOrig.w" "groupParts2.ig";
connectAttr "groupId2.id" "groupParts2.gi";
connectAttr "relativeCorrectorsSG.pa" ":renderPartition.st" -na;
connectAttr "absoluteCorrectorsSG.pa" ":renderPartition.st" -na;
connectAttr "relativeCorrectors_mat.msg" ":defaultShaderList1.s" -na;
connectAttr "absoluteCorrectors_mat.msg" ":defaultShaderList1.s" -na;
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
connectAttr "bShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "aShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "baseShape.iog" ":initialShadingGroup.dsm" -na;
// End of combinationCube.ma
