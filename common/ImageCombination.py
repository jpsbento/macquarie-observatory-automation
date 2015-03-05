def image_combine(INPUT,output_name,operation='median'):
    """ Combine images using a specific operation 
    INPUTS:
        INPUT -- files to read in, can be a format like such
            1. (list) list of filenames to load, OR
            2. (str)  filename to load, OR 
            .  (ndarray) Numpy array of data, already loaded, make sure 0 axis loops through data sets

        output_name (str) -- name of combined image

        operation (str) -- how images are to be combined
            1. median (default)
            2. mean 
            3. sum
                    
    OUTPUS:
        output_name (.fits) FITS image that is a combination of specified input images
         &
        Function returns True if the file was made properly otherwise False        
    
    EXAMPLE:
        bias_list = ['bias.0001.fits','bias.0002.fits']
        did_it_do_it = combine_image(bias_list,'superbias.fits')
        if did_it_do_it: print "images were combined!"
           OR
        bias_list = 'bias.list'
        did_it_do_it = combine_image(bias_list,'superbias.fits','mean')
        if did_it_do_it: print "images were combined!"
        

        Example contents of bias.list (without all the lines of course)
        ----------------    
        |bias.0001.fits|       bias.list can be made with a cmd like
        |bias.0002.fits|        'ls bias*.fits > bias.list'
        |bias.0003.fits|
        ----------------

    10/04/2013 18:35:15 KAP: Created
    """
    import pyfits
    import numpy as np
    from os import path
    
    # If a data cube was input
    if isinstance(INPUT, np.ndarray): 
        print "CI:data cube not supported yet...abort"
        return False
        """for i in range(0,len(file_list)):
            if i == 0:  # get size
                nx = pyfits.getval(file_list[0], 'NAXIS1')
                ny = pyfits.getval(file_list[0], 'NAXIS2')
                all_data = np.ndarray(shape=(len(file_list),nx,ny))
            if file_list.shape[1] == nx and img_data.shape[2] == ny: # FIXME check this
                all_data[i] = file_list[i]
            else:
                print "Combine_Image: images are different sizes. Will not be able to combine. aborting"
                del all_data, img_data
                return False
        """
    elif isinstance(INPUT,np.string_) or isinstance(INPUT,str) or isinstance(INPUT, list):
        # decompose file with image names in it to list        
        if isinstance(INPUT,np.string_) or isinstance(INPUT,str):        
            if not path.isfile(INPUT): print "CI: file",INPUT,"not found. abort"; return False
            da_imgs = [line.strip() for line in open(INPUT)] # reads lines and scraps '\n' at end
            INPUT = da_imgs # reassign for loop later
            del da_imgs
        
        # Do work to get data     
        for i in range(0,len(INPUT)):
            if not path.isfile(INPUT[i]): print "CI: file",INPUT[i],"not found. abort"; return False
            if i == 0:  # get size on first iteration only
                nx = pyfits.getval(INPUT[0], 'NAXIS1')
                ny = pyfits.getval(INPUT[0], 'NAXIS2')
                all_data = np.ndarray(shape=(len(INPUT),ny,nx))
            img_data = pyfits.getdata(INPUT[i])
            if img_data.shape[1] == nx and img_data.shape[0] == ny:
                all_data[i] = img_data 
            else:
                print "CI: images are different sizes. Will not be able to combine. abort"
                del all_data, img_data
                return False
    else:
        print "CI: input images are the wrong type. abort"
        return False

    # Combine Images with some operations 
    if operation == 'median':
        combined_data = np.median( all_data,axis=0 )
    elif operation == 'mean':
        combined_data = np.mean( all_data,axis=0 )
    elif operation == 'sum':
        combined_data = np.sum( all_data,axis=0 )
    else:
        print "CI: operation type not recognized. aborting"
        return False

    # Write data to new file    
    new_image = pyfits.PrimaryHDU(combined_data)
    new_image.writeto(output_name,clobber=True)
    print output_name,"was created using a",operation,"operation."
    del all_data, img_data # clear up some memory
    return True
