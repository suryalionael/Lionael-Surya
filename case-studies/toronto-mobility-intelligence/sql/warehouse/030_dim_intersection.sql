TRUNCATE analytics.dim_intersection CASCADE;

INSERT INTO analytics.dim_intersection
    (px, main_street, side1_street, side2_street, signal_system, control_mode,
     audible_ped_signal, led_blankout_sign, transit_preempt, fire_preempt, rail_preempt,
     activation_date, geom)
SELECT
    px, main_street, side1_street, side2_street, signal_system, control_mode,
    audible_ped_signal, led_blankout_sign, transit_preempt, fire_preempt, rail_preempt,
    activation_date, geom
FROM clean.intersections;
