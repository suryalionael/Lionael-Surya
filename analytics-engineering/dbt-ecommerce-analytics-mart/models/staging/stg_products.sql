with source as (

    select * from {{ source('raw', 'olist_products') }}

),

renamed as (

    select
        product_id,
        product_category_name,
        product_name_lenght::int as product_name_length,
        product_description_lenght::int as product_description_length,
        product_photos_qty::int as product_photos_qty,
        product_weight_g::numeric as product_weight_g,
        product_length_cm::numeric as product_length_cm,
        product_height_cm::numeric as product_height_cm,
        product_width_cm::numeric as product_width_cm

    from source

)

select * from renamed
