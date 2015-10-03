gimp_exec = """gimp -i -d -f -b '(
    let* (
        (colors (list <COLORS>))
                      
        (sizes (list <SIZES>))
        
        (borderx <BORDERX>) ; the border to cut off at the right side when resizing
        (bordery <BORDERY>) ; the border to cut off at the bottom when resizing
        
        (image (car (gimp-file-load RUN-NONINTERACTIVE "<GIMP_IMAGE>" "<GIMP_IMAGE>")))
        (hmask (car (gimp-image-get-layer-by-name image (string-append "<MASK_PREFIX>" "horizontal"))))
        (vmask (car (gimp-image-get-layer-by-name image (string-append "<MASK_PREFIX>" "vertical"))))
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
            (set! color (string-append "<COLOR_PREFIX>" (car colors)))
            (set! fname (string-append (car colors) "<EXPORT_SUFFIX>"))
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
                (gimp-layer-resize copy_flattened w h 0 0)
                (file-png-save RUN-NONINTERACTIVE image_size copy_flattened path path 0 9 0 0 0 0 0)
                
                (set! sizes_ (cdr sizes_))
            )
            (set! colors (cdr colors))
        )
    )

)' -b '(gimp-quit 0)'"""
