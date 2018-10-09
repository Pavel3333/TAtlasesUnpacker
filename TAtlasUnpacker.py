from copy import copy, deepcopy

from os import listdir
from sys import argv

from struct import unpack

def unpack_uint32_t(string):
    return unpack('<I', string)[0]

def unpack_uint64_t(string):
    return unpack('<Q', string)[0]

ATLAS_EXT = 'atlas_processed'

coord_struct = {
    'x0'        : 0,  #x0 coord                                 | uint32_t
    'x1'        : 0,  #x1 coord                                 | uint32_t
    'y0'        : 0,  #y0 coord                                 | uint32_t
    'y1'        : 0,  #y1 coord                                 | uint32_t
    'path'      : ''  #path
}

atlas_struct = {
    'header' : {
        '00->03'    : 0,  #some const flag (true always)            | uint32_t
        'WIDTH'     : 0,  #W resolution                             | uint32_t
        'HEIGHT'    : 0,  #H resolution                             | uint32_t
        '12->15'    : 0,  #some not const flag, perhaps compression | uint32_t
        '16->19'    : '', #const 'BCVT' string                      | char[4]
        '20->23'    : 0,  #some const flag (true always)            | uint32_t
        'SIZE'      : 0L  #DDS size                                 | uint64_t
    },
    'DDS'    : '',        #DDS section                              | char[XX]
    'coords' : []
}

atlases = {}

args = []
argv_ctr = 0
if(len(argv) > 1):
    print 'Drag and Drop checking: TRUE;'
    args = argv[1:]
    argv_ctr = len(argv)
else:
    print 'Drag and Drop checking: FALSE;'
    print 'Unpacking all *.atlas_processed files in current folder'
    args = listdir('./')
    argv_ctr = len(args)


for i in xrange(0, argv_ctr):        
    path = args[i] #.split('\\')[-1]
    
    if path.endswith(ATLAS_EXT):
        atlas = deepcopy(atlas_struct)

        atlases[path] = atlas
        
        atlas_header = atlas['header']
        
        with open(path, 'rb') as atlas_packed:

            atlas_packed.seek(0, 2) #seek the eof position
            atlas_size = atlas_packed.tell()
            atlas_packed.seek(0, 0) #seek the file start
            
            if atlas_size > 32: #check if file size more than header size
                atlas_read = atlas_packed.read
                
                atlas_header['00->03'] = unpack_uint32_t(atlas_read(4))
                atlas_header['WIDTH']  = unpack_uint32_t(atlas_read(4)) #width  of image in bits
                atlas_header['HEIGHT'] = unpack_uint32_t(atlas_read(4)) #height of image in bits
                atlas_header['12->15'] = unpack_uint32_t(atlas_read(4))
                atlas_header['16->19'] = atlas_read(4)
                atlas_header['20->23'] = unpack_uint32_t(atlas_read(4))
                atlas_header['SIZE']  = unpack_uint64_t(atlas_read(8))

                if(atlas_header['00->03']           and
                   atlas_header['WIDTH']            and
                   atlas_header['HEIGHT']           and
                   atlas_header['16->19'] == 'BCVT' and
                   atlas_header['20->23']           and
                   atlas_header['SIZE']
                ):
                    atlas['DDS'] = atlas_read(atlas_header['SIZE'])

                    while(atlas_packed.tell() != atlas_size):                        
                        coord_sect = copy(coord_struct)

                        coord_sect['x0'] = unpack_uint32_t(atlas_read(4))
                        coord_sect['x1'] = unpack_uint32_t(atlas_read(4))
                        coord_sect['y0'] = unpack_uint32_t(atlas_read(4))
                        coord_sect['y1'] = unpack_uint32_t(atlas_read(4))
                        
                        symbol = atlas_read(1)
                
                        coord_sect['path'] += symbol
                
                        while(symbol != '\x00'):
                            symbol = atlas_read(1)
                            
                            if(symbol != '\x00'):
                                coord_sect['path'] += symbol
                        
                        atlas['coords'].append(coord_sect)
print 'Parsing successfully completed!'

for fil in atlases:
    with open(fil.replace(ATLAS_EXT, '.dds'), 'wb') as texture:
        texture.write(atlases[fil]['DDS'])

print 'DDS textures successfully unpacked!'

for fil in atlases:
    print '\n%s:'%(fil)

    atlas = atlases[fil]
    print '\theader:'

    header = atlas['header']
    
    print '\t\tresolution : %sx%s'    %(header['WIDTH'] // 8, header['HEIGHT'] // 8) #converting from bits to bytes
    print '\t\tsize       : %s Bytes' %(header['SIZE'])
        
    print '\tcoords:'

    coord_i = 0
    
    for coord in atlas['coords']:
        print '\t\tcoord_%s:'%(coord_i)

        print '\t\t\tx    : %-4s->%-4s'%(coord['x0'] // 8, coord['x1'] // 8) #converting from bits to bytes
        print '\t\t\ty    : %-4s->%-4s'%(coord['y0'] // 8, coord['y1'] // 8) #converting from bits to bytes
        print ''
        print '\t\t\tpath : %s'%(coord['path'])
        
        coord_i += 1

input() #wait for user action
