#! /usr/bin/env python
import os, sys
from lxml import etree
from copy import deepcopy
from shutil import copyfile, rmtree
from opcdiag.controller import OpcController


def duplicate_pptx_sheet(filename, slide_number, filename_output=None):
    """
    A method that duplicates a slide in a PowerPoint file

    Parameters
    ----------
    filename : string
        The filename contains the location of the original powerpoint file that
        will have a slide duplicated.

    slide_number : int
        The slide_number is the index of the slide that is supposed to be
        duplicated in the powerpoint file.
        Note: The index starts counting from 1 NOT 0

    filename_output : string
        The filename_output is the name of the file that will be created.
        Note: If the filename_output is not supplied, then the input file
              get's owerridden.

    Returns : nothing
    """

    if filename_output is None:
        filename_output = filename

    # Step 1. Extract filename & filename_output
    opc = OpcController()
    TEMP_FOLDER_SOURCE = filename.replace(".pptx", '')
    opc.extract_package(filename, TEMP_FOLDER_SOURCE)

    TEMP_FOLDER_TARGET = filename_output.replace(".pptx", '')
    opc.extract_package(filename_output, TEMP_FOLDER_TARGET)

    # Step 2. Find the next_slide_id of filename_output
    slides_list = [x for x in os.listdir("{}/ppt/slides/".format(TEMP_FOLDER_TARGET))
                   if '.xml' in x]
    slides_count = len(slides_list)
    next_slide_id = slides_count + 1

    # Step 3. Copy the oldslide and it's relationship
    xml_slide = "{}/ppt/slides/slide{}.xml"
    xml_slide_rel = "{}/ppt/slides/_rels/slide{}.xml.rels"
    copyfile(xml_slide.format(TEMP_FOLDER_SOURCE, slide_number),
             xml_slide.format(TEMP_FOLDER_TARGET, next_slide_id))
    copyfile(xml_slide_rel.format(TEMP_FOLDER_SOURCE, slide_number),
             xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id))


    replaceString = {}
    # Step 3-1 Find the oleObject and related data files.
    # Get the oleObject#.bin file from the slide relation (hacky indeed)
    with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id)) as file:
        lines = [line for line in file.readlines() if '/embeddings/oleObject' in line]

    # Paths where the files are
    bin_oleObject = "{}/ppt/embeddings/oleObject{}.bin"

    # If there are no oleObject in this slide, no need to do the files/data copying
    if len(lines) > 0:
        for line in lines:
            # Step 5. Find the oleObject_id
            # example: oleObject1.bin, oleObject2.bin, oleObject3.bin
            oleObject_filename = line.split('Target="../embeddings/')[-1].replace('"/>\n', '')
            oleObject_id = int(oleObject_filename.replace('oleObject', '').replace('.bin', ''))

            # Step 6. Find the next_oleObject_id
            try:
                oleObject_list = [x for x in os.listdir("{}/ppt/embeddings/".format(TEMP_FOLDER_TARGET))
                               if 'oleObject' in x]
                next_oleObject_id = len(oleObject_list) + 1
            except:
                #no embeddings folder
                os.mkdir("{}/ppt/embeddings".format(TEMP_FOLDER_TARGET))
                next_oleObject_id = 1;


            copyfile(bin_oleObject.format(TEMP_FOLDER_SOURCE, oleObject_id),
                     bin_oleObject.format(TEMP_FOLDER_TARGET, next_oleObject_id))

            # Step 10. Replace the Target attribute in the slide#.xml.rel
            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'r') as slide_rel:
                xml_slide_rel_file = slide_rel.read()

            xml_slide_rel_file = xml_slide_rel_file.replace(
                'oleObject{}.bin'.format(oleObject_id),
                'oleObject{}.bin'.format(next_oleObject_id)
            )

            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'w') as slide_rel:
                slide_rel.write(xml_slide_rel_file)


    # Step 3-2 Find the image and related data files.
    # Get the image#.xxx file from the slide relation (hacky indeed)
    with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id)) as file:
        lines = [line for line in file.readlines() if '/media/image' in line]

    # Paths where the files are
    xxx_image = "{}/ppt/media/image{}.{}"

    # If there are no image in this slide, no need to do the files/data copying
    if len(lines) > 0:
        for line in lines:
            # Step 5. Find the image_id and ext
            # example: image1.xxx, image2.xxx, image3.xxx
            image_filename = line.split('Target="../media/')[-1].replace('"/>\n', '')
            image_id = int(image_filename.replace('image', '').split(".")[0])
            image_ext = image_filename.replace('image', '').split(".")[1]

            # Step 6. Find the next_image_id
            try:
                image_list = [x for x in os.listdir("{}/ppt/media/".format(TEMP_FOLDER_TARGET))
                               if 'image' in x]
                next_image_id = len(image_list) + 1
            except:
                #no media folder
                os.mkdir("{}/ppt/media".format(TEMP_FOLDER_TARGET))
                next_image_id = 1;


            copyfile(xxx_image.format(TEMP_FOLDER_SOURCE, image_id, image_ext),
                     xxx_image.format(TEMP_FOLDER_TARGET, next_image_id, image_ext))

            # Step 10. Replace the Target attribute in the slide#.xml.rel
            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'r') as slide_rel:
                xml_slide_rel_file = slide_rel.read()

            xml_slide_rel_file = xml_slide_rel_file.replace(
                'image{}.{}'.format(image_id, image_ext),
                'image{}.{}'.format(next_image_id, image_ext)
            )

            replaceString["/media/image{}.{}".format(image_id, image_ext)] = "/media/image{}.{}".format(next_image_id, image_ext)

            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'w') as slide_rel:
                slide_rel.write(xml_slide_rel_file)



    # Step 3-3 Find the drawingfile and related data files.
    # Get the vmlDrawing#.vml file from the slide relation (hacky indeed)
    with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id)) as file:
        lines = [line for line in file.readlines() if '/drawings/vmlDrawing' in line]

    # Paths where the files are
    vml_Drawing = "{}/ppt/drawings/vmlDrawing{}.vml"
    vml_Drawing_rel = "{}/ppt/drawings/_rels/vmlDrawing{}.vml.rels"

    # If there are no vmlDrawing in this slide, no need to do the files/data copying
    if len(lines) > 0:
        for line in lines:
            # Step 5. Find the vmlDrawing_id
            # example: vmlDrawing1.vml, vmlDrawing2.vml, vmlDrawing3.vml
            vmlDrawing_filename = line.split('Target="../drawings/')[-1].replace('"/>\n', '')
            vmlDrawing_id = int(vmlDrawing_filename.replace('vmlDrawing', '').replace('.vml', ''))

            # Step 6. Find the next_vmlDrawing_id
            try:
                vmlDrawing_list = [x for x in os.listdir("{}/ppt/drawings/".format(TEMP_FOLDER_TARGET))
                               if 'vmlDrawing' in x]
                next_vmlDrawing_id = len(vmlDrawing_list) + 1
            except:
                #no drawings folder
                os.mkdir("{}/ppt/drawings".format(TEMP_FOLDER_TARGET))
                os.mkdir("{}/ppt/drawings/_rels".format(TEMP_FOLDER_TARGET))
                next_vmlDrawing_id = 1;


            copyfile(vml_Drawing.format(TEMP_FOLDER_SOURCE, vmlDrawing_id),
                     vml_Drawing.format(TEMP_FOLDER_TARGET, next_vmlDrawing_id))
            copyfile(vml_Drawing_rel.format(TEMP_FOLDER_SOURCE, vmlDrawing_id),
                     vml_Drawing_rel.format(TEMP_FOLDER_TARGET, next_vmlDrawing_id))

            #check if vml_Drawing_rel file contains replace string
            with open(vml_Drawing_rel.format(TEMP_FOLDER_TARGET, next_vmlDrawing_id), 'r') as drawing_rel:
                xml_drawing_rel_file = drawing_rel.read()

            for key in replaceString.keys():
            	xml_drawing_rel_file = xml_drawing_rel_file.replace(key, replaceString[key])

            with open(vml_Drawing_rel.format(TEMP_FOLDER_TARGET, next_vmlDrawing_id), 'w') as drawing_rel:
                drawing_rel.write(xml_drawing_rel_file)

            # Step 10. Replace the Target attribute in the slide#.xml.rel
            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'r') as slide_rel:
                xml_slide_rel_file = slide_rel.read()

            xml_slide_rel_file = xml_slide_rel_file.replace(
                'vmlDrawing{}.vml'.format(vmlDrawing_id),
                'vmlDrawing{}.vml'.format(next_vmlDrawing_id)
            )

            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'w') as slide_rel:
                slide_rel.write(xml_slide_rel_file)

    # Step 4 Find the chartfile and related data files.
    # Get the chart#.xml file from the slide relation (hacky indeed)
    with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id)) as file:
        lines = [line for line in file.readlines() if '/charts/chart' in line]

    # Paths where the files are
    xml_chart = "{}/ppt/charts/chart{}.xml"
    xml_style = "{}/ppt/charts/style{}.xml"
    xml_colors = "{}/ppt/charts/colors{}.xml"
    xml_chart_rel = "{}/ppt/charts/_rels/chart{}.xml.rels"
    xml_xlsx = "{}/ppt/embeddings/Microsoft_Excel_Worksheet{}.xlsx"

    # This gets populated with lxml Elements, they will go into [Content_Types].xml
    content_types = [
        etree.XML('<Override PartName="/ppt/slides/slide{}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'.format(
            next_slide_id
        ))
    ]

    # If there are no charts in this slide, no need to do the files/data copying
    if len(lines) > 0:
        for line in lines:
            # Reset the filenames. The files are not always in the pptx file.
            style_filename = None
            colors_filename = None
            xlsx_filename = None

            # Step 5. Find the chart_id
            # example: chart1.xml, chart2.xml, chart3.xml
            chart_filename = line.split('Target="../charts/')[-1].replace('"/>\n', '')
            chart_id = int(chart_filename.replace('chart', '').replace('.xml', ''))

            # Step 6. Find the next_chart_id
            try:
                chart_list = [x for x in os.listdir("{}/ppt/charts/".format(TEMP_FOLDER_TARGET))
                               if 'chart' in x]
                next_chart_id = len(chart_list) + 1
            except:
                #no charts folder
                os.mkdir("{}/ppt/charts".format(TEMP_FOLDER_TARGET))
                next_chart_id = 1;
            

            # Step 7. Get the style#.xml, colors#.xml and #.xlsx filenames and ids
            with open(xml_chart_rel.format(TEMP_FOLDER_SOURCE, chart_id)) as file:
                for line in file.readlines():
                    if 'Target="style' in line:
                        style_filename = line.split('Target="')[-1].replace('"/>\n', '')
                        style_id = style_filename.replace('style', '').replace('.xml', '')
                    if 'Target="colors' in line:
                        colors_filename = line.split('Target="')[-1].replace('"/>\n', '')
                        colors_id = colors_filename.replace('colors', '').replace('.xml', '')
                    elif 'Target="../embeddings' in line:
                        xlsx_filename = line.split('Target="../embeddings/')[-1].replace('"/>\n', '')
                        xlsx_id = xlsx_filename.replace('Microsoft_Excel_Worksheet', '').replace('.xlsx', '')

            # Step 8. Copy the charts, styles, colors, xlsx and rel files.
            # Note: The "-1" id's are used later to skip checking if the id
            # exists. The replace method won't find the -1 ids, so it skips them.
            if style_filename is not None:
                next_style_id = len([f for f
                                     in os.listdir('{}/ppt/charts/'.format(TEMP_FOLDER_TARGET))
                                     if 'style' in f]) + 1
                copyfile(xml_style.format(TEMP_FOLDER_SOURCE, style_id),
                         xml_style.format(TEMP_FOLDER_TARGET, next_style_id))
                content_types.append(
                    etree.XML(
                          '<Override PartName="/ppt/charts/style{}.xml" ContentType="application/vnd.ms-office.chartstyle+xml"/>'.format(
                            next_style_id
                        )
                    )
                )
            else:
                style_id = "-1"
                next_style_id = "-1"

            if colors_filename is not None:
                next_colors_id = len([f for f
                                      in os.listdir('{}/ppt/charts/'.format(TEMP_FOLDER_TARGET))
                                      if 'colors' in f]) + 1
                copyfile(xml_colors.format(TEMP_FOLDER_SOURCE, colors_id),
                         xml_colors.format(TEMP_FOLDER_TARGET, next_colors_id))
                content_types.append(
                    etree.XML(
                          '<Override PartName="/ppt/charts/colors{}.xml" ContentType="application/vnd.ms-office.chartcolorstyle+xml"/>'.format(
                            next_colors_id
                        )
                    )
                )
            else:
                colors_id = "-1"
                next_colors_id = "-1"

            if xlsx_filename is not None:
                next_xlsx_id = len([f for f in os.listdir('{}/ppt/embeddings/'.format(TEMP_FOLDER_TARGET))]) + 1
                copyfile(xml_xlsx.format(TEMP_FOLDER_SOURCE, xlsx_id),
                         xml_xlsx.format(TEMP_FOLDER_TARGET, next_xlsx_id))
            else:
                xlsx_id = "-1"
                next_xlsx_id = "-1"

            copyfile(xml_chart.format(TEMP_FOLDER_SOURCE, chart_id),
                     xml_chart.format(TEMP_FOLDER_TARGET, next_chart_id))
            copyfile(xml_chart_rel.format(TEMP_FOLDER_SOURCE, chart_id),
                     xml_chart_rel.format(TEMP_FOLDER_TARGET, next_chart_id))

            # NOTE: All files exist at this stage, now we start replacing them
            #       with correct values/indexes.
            # Step 9. Replace the id's in the chart relationship file
            with open(xml_chart_rel.format(TEMP_FOLDER_TARGET, next_chart_id), 'r') as chart_rel:
                xml_chart_rel_file = chart_rel.read()

            # This is where the "-1" id whon't be found and thusly skipped.
            xml_chart_rel_file = xml_chart_rel_file.replace(
                'style{}.xml'.format(style_id),
                'style{}.xml'.format(next_style_id)
            ).replace(
                'colors{}.xml'.format(colors_id),
                'colors{}.xml'.format(next_colors_id)
            ).replace(
                'Microsoft_Excel_Worksheet{}.xlsx'.format(xlsx_id),
                'Microsoft_Excel_Worksheet{}.xlsx'.format(next_xlsx_id)
            )

            with open(xml_chart_rel.format(TEMP_FOLDER_TARGET, next_chart_id), 'w') as chart_rel:
                chart_rel.write(xml_chart_rel_file)

            # Step 10. Replace the Target attribute in the slide#.xml.rel
            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'r') as slide_rel:
                xml_slide_rel_file = slide_rel.read()

            xml_slide_rel_file = xml_slide_rel_file.replace(
                'chart{}.xml'.format(chart_id),
                'chart{}.xml'.format(next_chart_id)
            )

            with open(xml_slide_rel.format(TEMP_FOLDER_TARGET, next_slide_id), 'w') as slide_rel:
                slide_rel.write(xml_slide_rel_file)

            # Step 11. Add the chart lxml Element into the content_types container.
            content_types.append(
                etree.XML(
                    '<Override PartName="/ppt/charts/chart{}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>'.format(
                        next_chart_id
                    )
                )
            )


    # Step 12. Add the newly created content to the [Content_Types].xml file
    tree = etree.parse('{}/[Content_Types].xml'.format(TEMP_FOLDER_TARGET))
    root = tree.getroot()
    for element in content_types:
        root.append(element)

    with open('{}/[Content_Types].xml'.format(TEMP_FOLDER_TARGET), 'w') as file:
        # Hack :: Inject the top tag [<?xml ...] back into the file.
        #         (Can't do it with lxml?)
        file.writelines(
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>{}".format(
                etree.tostring(root)
            )
        )

    # Step 13. Find the next slide presentation relation id and add a new
    #          relation to the presentation.xml.rels relationship file
    tree = etree.parse('{}/ppt/_rels/presentation.xml.rels'.format(TEMP_FOLDER_TARGET))
    root = tree.getroot()
    next_slide_rid = len(root.getchildren()) + 1
    root.append(
        etree.XML(
            '<Relationship Id="rId{}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{}.xml"/>'.format(
                next_slide_rid,
                next_slide_id
            )
        )
    )
    with open('{}/ppt/_rels/presentation.xml.rels'.format(TEMP_FOLDER_TARGET), 'w') as file:
        # Hack :: Inject the top tag [<?xml ...] back into the file.
        #         (Can't do it with lxml?)
        file.writelines(
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>{}".format(
                etree.tostring(root)
            )
        )

    # Step 14. Add the new relation id (from Step 13) and a new id to the
    #          presentation.xml.
    tree = etree.parse('{}/ppt/presentation.xml'.format(TEMP_FOLDER_TARGET))
    root = tree.getroot()
    sldIdLst = root.find(
        './/p:sldIdLst',
        {'p': "http://schemas.openxmlformats.org/presentationml/2006/main"}
    )
    sldId = deepcopy(sldIdLst.getchildren()[0])  # get the first child
    sldId.attrib['id'] = unicode(max([int(x.attrib['id']) for x in sldIdLst]) + 1)
    sldId.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'] = "rId{}".format(next_slide_rid)
    sldIdLst.append(sldId)

    with open('{}/ppt/presentation.xml'.format(TEMP_FOLDER_TARGET), 'w') as file:
        # Hack :: Inject the top tag [<?xml ...] back into the file.
        #         (Can't do it with lxml?)
        file.writelines(
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>{}".format(
                etree.tostring(root)
            )
        )

    # Step 15. Edit docProps/app.xml
    # tree = etree.parse('{}/docProps/app.xml'.format(TEMP_FOLDER_TARGET))
    # root = tree.getroot()
    # Paragraphs = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Paragraphs")
    # Paragraphs.text = unicode(int(Paragraphs.text) + 2)
    # Slides = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Slides")
    # Slides.text = unicode(int(Slides.text) + 1)
    # HeadingPairs = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}HeadingPairs")
    # vector = HeadingPairs.find("{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}vector")
    # vt = vector.getchildren()[7].getchildren()[0]
    # vt.text = unicode(int(vt.text) + 1)
    # TitlesOfParts = root.find("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}TitlesOfParts")
    # vector = TitlesOfParts.getchildren()[0]
    # vector.attrib["size"] = unicode(int(vector.attrib["size"]) + 1)
    # lpstr = deepcopy(vector.getchildren()[len(vector) - 1])
    # vector.append(lpstr)

    with open('{}/docProps/app.xml'.format(TEMP_FOLDER_TARGET), 'w') as file:
        # Hack :: Inject the top tag [<?xml ...] back into the file.
        #         (Can't do it with lxml?)
        file.writelines(
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>{}".format(
                etree.tostring(root)
            )
        )

    opc.repackage(TEMP_FOLDER_TARGET, filename_output)

    rmtree(TEMP_FOLDER_TARGET)
    rmtree(TEMP_FOLDER_SOURCE)

target_path = sys.argv[1]
copy_path = sys.argv[2]
copy_index = int(sys.argv[3])

duplicate_pptx_sheet(copy_path, copy_index, target_path)
print("")
