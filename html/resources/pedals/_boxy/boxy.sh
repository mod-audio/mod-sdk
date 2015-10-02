#!/bin/bash

# This generator takes a special GIMP file and generates different
# PNG images from it.
# The source must contain some hidden layers with a special prefix in
# their name. The script loops over those layers taking the following
# actions:
#     * layer is set to visible
#     * all visible layers are merged
#     * the result together with two (hidden) b/w masks are copied to new image
#     * the result gets resized the following way (e.g. horizontal):
#         * the base layer is copied and a mask is applied
#         * the base layer gets cropped by the necessary amount of pixels
#           plus borderx from the right
#         * the masked copy is translated by the necessary amount of pixels
#           to the left
#         * the masked copy is merged onto the base layer
#         * the masks are deleted
#         * the image is exported to its final destination as PNG

gimp_image="boxy.xcf"
color_prefix="color_"
mask_prefix="mask_"
export_suffix=".png"

gimp -i -d -f -b '(
    let* (
        (colors (list "black" ; all color layers in the source gimp file (name without prefix)
                      "blue"
                      "brown"
                      "cream"
                      "cyan"
                      "darkblue"
                      "gray"
                      "green"
                      "none"
                      "orange"
                      "petrol"
                      "pink"
                      "purple"
                      "racing"
                      "red"
                      "white"
                      "wood0"
                      "wood1"
                      "wood2"
                      "wood3"
                      "wood4"
                      "yellow"
                      "zinc"))
                      
        (sizes (list  (list (list 230 431) "../boxy/") ; all final sizes with their respective folders
                      (list (list 326 431) "../boxy75/")
                      (list (list 364 431) "../boxy85/")
                      (list (list 421 431) "../boxy100/")
                      (list (list 301 315) "../boxy-small/")))
        
        (borderx 12) ; the border to cut off at the right side when resizing
        (bordery 29) ; the border to cut off at the bottom when resizing
        
        (image (car (gimp-file-load RUN-NONINTERACTIVE "'$gimp_image'" "'$gimp_image'")))
        (hmask (car (gimp-image-get-layer-by-name image (string-append "'$mask_prefix'" "horizontal"))))
        (vmask (car (gimp-image-get-layer-by-name image (string-append "'$mask_prefix'" "vertical"))))
        (width (car (gimp-image-width image)))
        (height (car (gimp-image-height image)))
        (image_color ())
        (image_size ())
        (color_layer -1)
        (origin_flattened -1)
        (copy_flattened -1)
        (base_layer -1)
        (border_layer -1)
        (border_mask -1)
        (floating -1)
        (color "")
        (fname "")
        (i 0)
        (w 0)
        (h 0)
        (size ())
        (sizes_ ())
        (path "")
    )
    ; loop colors
    (while (not (null? colors))
        (begin
            (set! image_color (car (gimp-channel-ops-duplicate image)))
            (set! color (string-append "'$color_prefix'" (car colors)))
            (set! fname (string-append (car colors) "'$export_suffix'"))
            (set! color_layer (car (gimp-image-get-layer-by-name image_color color)))
            
            (gimp-message (string-append "PROCESSING: " color " (#" (number->string color_layer) ")"))
            
            (gimp-item-set-visible color_layer 1)
            (set! origin_flattened (car (gimp-image-merge-visible-layers image_color CLIP-TO-IMAGE)))
            
            (set! i 0)
            (set! sizes_ sizes)
            (while (not (null? sizes_))
                (set! size (car sizes_))
                (set! w (caar size))
                (set! h (cadar size))
                (set! path (string-append (cadr size) fname))
                
                (gimp-message (string-append "    " (number->string w) "x" (number->string h) " -> " path))
                
                (gimp-edit-copy origin_flattened)
                (set! image_size (car (gimp-edit-paste-as-new)))
                (set! base_layer (car (gimp-image-get-active-layer image_size)))
                
                (if (< w (car (gimp-image-width image_size))) (begin
                    
                    (gimp-message (string-append "        resize horizontally " (number->string width) " -> " (number->string w)))
                    
                    (set! border_layer (car (gimp-layer-copy base_layer 1)))
                    (gimp-image-insert-layer image_size border_layer 0 -1)
                    (set! border_mask (car (gimp-layer-create-mask border_layer ADD-WHITE-MASK)))
                    (gimp-layer-add-mask border_layer border_mask)
                    (gimp-edit-copy hmask)
                    (set! floating (car (gimp-edit-paste border_mask 1)))
                    (gimp-floating-sel-anchor floating)
                    (gimp-layer-remove-mask border_layer MASK-APPLY)
                    (gimp-layer-translate border_layer (- 0 (- width w)) 0)
                
                    (gimp-layer-resize base_layer (- w borderx) height 0 0)
                ))
                
                (set! base_layer (car (gimp-image-merge-visible-layers image_size CLIP-TO-IMAGE)))
                
                (if (< h (car (gimp-image-height image_size))) (begin
                    
                    (gimp-message (string-append "        resize vertically " (number->string height) " -> " (number->string h)))
                    
                    (set! border_layer (car (gimp-layer-copy base_layer 1)))
                    (gimp-image-insert-layer image_size border_layer 0 -1)
                    (set! border_mask (car (gimp-layer-create-mask border_layer ADD-WHITE-MASK)))
                    (gimp-layer-add-mask border_layer border_mask)
                    (gimp-edit-copy vmask)
                    (set! floating (car (gimp-edit-paste border_mask 1)))
                    (gimp-floating-sel-anchor floating)
                    (gimp-layer-remove-mask border_layer MASK-APPLY)
                    (gimp-layer-translate border_layer 0 (- 0 (- height h)))
                
                    (gimp-layer-resize base_layer width (- h bordery) 0 0)
                ))
                
                (set! copy_flattened (car (gimp-image-merge-visible-layers image_size CLIP-TO-IMAGE)))
                
                (file-png-save RUN-NONINTERACTIVE image_size copy_flattened path path 0 9 0 0 0 0 0)
                
                (set! sizes_ (cdr sizes_))
            )
            (set! colors (cdr colors))
        )
    )

)' -b '(gimp-quit 0)'
