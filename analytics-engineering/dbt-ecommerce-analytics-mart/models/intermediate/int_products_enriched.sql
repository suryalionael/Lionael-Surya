with products as (

    select * from {{ ref('stg_products') }}

),

translations as (

    select * from {{ ref('stg_product_category_translation') }}

),

joined as (

    select
        products.product_id,
        coalesce(
            translations.product_category_name_english,
            products.product_category_name,
            'unknown'
        ) as category_name,
        products.product_weight_g,
        products.product_length_cm,
        products.product_height_cm,
        products.product_width_cm

    from products
    left join translations
        on products.product_category_name = translations.product_category_name

)

select * from joined
