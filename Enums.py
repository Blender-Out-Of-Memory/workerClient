from __future__ import annotations

from enum import Enum

class RenderOutputType(Enum):
    RGB = (".rgb", "Iris")
    JPG = (".jpg", "JPEG")
    JP2 = (".jp2", "JPEG 200 J2")
    J2C = (".j2c", "JPEG 200 J2K")
    PNG = (".png", "PNG")
    BMP = (".bmp", "BMP")
    TGA = (".tga", "TARGA")
    TGR = (".tga.r", "TARGA Raw")
    CIN = (".cin", "Cineon")
    DPX = (".dpx", "DPX")
    EXR = (".exr", "OpenEXR")
    MXR = (".exr.m", "OpenEXR Multilayer")
    HDR = (".hdr", "Radiance HDR")
    TIF = (".tif", "TIFF")
    WBP = (".webp", "WebP")
    AVJ = (".avi.j", "AVI JPEG")
    AVR = (".avi.r", "AVI RAW")

    # FFmpeg                     # Container (field 'type')
    MPG = (".mpg", "MPEG-1")     # 0
    DVD = (".dvd", "MPEG-2")     # 1
    MP4 = (".mp4", "MPEG-4")     # 2
    AVI = (".avi", "AVI")        # 3
    QKT = (".mov", "QuickTime")  # 4
    DV  = (".dv" , "DV")         # 5
    FLV = (".flv", "Flash")      # 8
    MKV = (".mkv", "Matroska")   # 9
    OGG = (".ogv", "OGG")        # 10
    WBM = (".webm", "WebM")      # 12

    def get_extension(self):
        # get index of second dot if exists
        additionalIndex = self.value[0].find(".", 1)
        end = additionalIndex if (additionalIndex != -1) else len(self.value[0])
        # chars after additionalIndex don't belong to extension
        return self.value[0][0:end]

    def is_video(self):
        return self in (RenderOutputType.AVJ, RenderOutputType.AVR, RenderOutputType.MPG, RenderOutputType.DVD,
                        RenderOutputType.MP4, RenderOutputType.AVI, RenderOutputType.QKT, RenderOutputType.DV,
                        RenderOutputType.FLV, RenderOutputType.MKV, RenderOutputType.OGG, RenderOutputType.WBM)

    @classmethod
    def from_identifier(cls, identifier: str):
        for element in RenderOutputType:
            if (element.value[0] == identifier):
                return element

        raise ValueError(f"{identifier} is no valid RenderOutputType")

class BlenderDataType(Enum):
    SingleFile = ("SINGL", "SingleFile")
    MultiFile = ("MULTI", "MultiFile")

    @classmethod
    def from_identifier(cls, identifier: str):
        for element in BlenderDataType:
            if (element.value[0] == identifier):
                return element

        raise ValueError(f"{identifier} is no valid BlenderDataType")

