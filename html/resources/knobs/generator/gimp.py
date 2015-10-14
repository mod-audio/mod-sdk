layer = """gimp -i -d -f -b '(
    let* (
        (image (car (gimp-file-load RUN-NONINTERACTIVE "<GIMP_IMAGE>" "<GIMP_IMAGE>")))
        (layer (car (gimp-image-get-layer-by-name image "<LAYER_NAME>")))
    )
    
    (if (not (= -1 layer)) (gimp-image-remove-layer image layer))
    (set! layer (car (gimp-file-load-layer RUN-NONINTERACTIVE image "<LAYER_SRC>")))
    (gimp-layer-set-name layer "<LAYER_NAME>")
    (gimp-layer-set-visible layer <LAYER_VISIBLE>)
    (gimp-image-insert-layer image layer 0 <LAYER_INDEX>)
    (gimp-file-save RUN-NONINTERACTIVE image layer "<GIMP_IMAGE>" "<GIMP_IMAGE>")
)' -b '(gimp-quit 0)'"""

mask = """gimp -i -d -f -b '(
    let* (
        (image (car (gimp-file-load RUN-NONINTERACTIVE "<GIMP_IMAGE>" "<GIMP_IMAGE>")))
        (mask (car (gimp-image-get-layer-by-name image "<MASK_LAYER>")))
        (layers (vector->list (cadr (gimp-image-get-layers image))))
        (layer -1)
        (mlayer -1)
        (name "")
    )
    (gimp-selection-all image)
    (gimp-edit-copy mask)
    (while (not (null? layers)) (begin
        (set! layer (car layers))
        (set! name (car (gimp-item-get-name layer)))
        (if (re-match "^<COLOR_PREFIX>.*" name) (begin
            (gimp-message (string-append "MASKING: "  name "(#" (number->string layer) ")"))
            (if (= -1 (car (gimp-layer-get-mask layer))) 
                (gimp-layer-add-mask layer (car (gimp-layer-create-mask layer ADD-WHITE-MASK)))
            )
            (gimp-context-set-background (list 0 0 0))
            (gimp-drawable-fill (car (gimp-layer-get-mask layer)) BACKGROUND-FILL)
            (gimp-floating-sel-anchor (car (gimp-edit-paste (car (gimp-layer-get-mask layer)) 1)))
        ))
        (set! layers (cdr layers))
    ))
    (gimp-file-save RUN-NONINTERACTIVE image layer "<GIMP_IMAGE>" "<GIMP_IMAGE>")
)' -b '(gimp-quit 0)'"""

colors = """gimp -i -d -f -b '(
    let* (
        (colors (list <COLORS>))
        (overlays (list <OVERLAYS>))
        
        (image (car (gimp-file-load RUN-NONINTERACTIVE "<GIMP_IMAGE>" "<GIMP_IMAGE>")))
        (image_color ())
        (color_layer -1)
        (over_layer -1)
        (mask_layer -1)
        (flattened -1)
        (floating -1)
        (mask -1)
        (color "")
        (over "")
        (fname "")
        (path "")
    )
    ; loop colors
    (while (not (null? colors)) (begin
        (set! image_color (car (gimp-channel-ops-duplicate image)))
        (set! color (string-append "<COLOR_PREFIX>" (car colors)))
        (set! over (car overlays))
        (set! fname (string-append (car colors) "<EXPORT_SUFFIX>"))
        (set! path (string-append "<CHDIR>" "/" fname))
        (set! color_layer (car (gimp-image-get-layer-by-name image_color color)))
        (set! over_layer (car (gimp-image-get-layer-by-name image_color over)))
        (set! mask_layer (car (gimp-image-get-layer-by-name image "<MASK_LAYER>")))
        
        (gimp-message (string-append "PROCESSING: " color " (#" (number->string color_layer) ")"))
        
        (gimp-item-set-visible color_layer 1)
        (if (not (= -1 over_layer)) (gimp-item-set-visible over_layer 1))
        
        ; MASK COLOR LAYER
        (if (not (= -1 mask_layer)) (begin
            (if (= -1 (car (gimp-layer-get-mask color_layer))) 
                (gimp-layer-add-mask color_layer (car (gimp-layer-create-mask color_layer ADD-WHITE-MASK)))
            )
            (gimp-selection-all image)
            (gimp-edit-copy mask_layer)
            (gimp-floating-sel-anchor (car (gimp-edit-paste (car (gimp-layer-get-mask color_layer)) 1)))
        ))
        
        (set! flattened (car (gimp-image-merge-visible-layers image_color CLIP-TO-IMAGE)))
        (file-png-save RUN-NONINTERACTIVE image_color flattened path path 0 9 0 0 0 0 0)
        (set! colors (cdr colors))
        (set! overlays (cdr overlays))
    ))

)' -b '(gimp-quit 0)'"""
