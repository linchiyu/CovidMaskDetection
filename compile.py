#include all modules that you want to compile
#run as follows
#python3 compile.py build_ext --inplace
#create a main.py and import the module compiled (.so or .pyd file)

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

compiled_path = 'compiled.'
ext_modules = [
    Extension(compiled_path+"cameramaskdetector",  ["cameramaskdetector.py"]),
    Extension(compiled_path+"utils.anchor_decode",  ["utils/anchor_decode.py"]),
    Extension(compiled_path+"utils.anchor_generator",  ["utils/anchor_generator.py"]),
    Extension(compiled_path+"utils.cameraThread",  ["utils/cameraThread.py"]),
    Extension(compiled_path+"utils.face_class",  ["utils/face_class.py"]),
    Extension(compiled_path+"utils.imgutil",  ["utils/imgutil.py"]),
    Extension(compiled_path+"utils.interface",  ["utils/interface.py"]),
    Extension(compiled_path+"utils.nms",  ["utils/nms.py"]),
    Extension(compiled_path+"load_model.tensorflow_loader",  ["load_model/tensorflow_loader.py"]),
#   ... all your modules that need be compiled ...
]
setup(
    name = 'ArticFoxMaskDetector',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)
