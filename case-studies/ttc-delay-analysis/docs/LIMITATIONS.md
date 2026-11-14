# Limitations

These are the limitations that matter for how the findings should be read.

1. **Reporting bias.** An incident only enters the data if someone reports
   it and a delay code is assigned. Quiet overnight delays and minor
   service adjustments may be under-reported.
2. **No ridership denominator.** A line with more incidents is not
   necessarily worse per rider. The data contain no boardings, vehicle
   kilometres, or service hours.
3. **No weather, construction, or staffing data.** Cause categories are
   broad. Weather and planned closures are partly absorbed into
   operations/external, so the cause effects are associations, not
   mechanisms.
4. **Cause labels change over time.** Legacy bus and streetcar files use
   coarse text labels; subway and 2025 data use TTC codes. A comparison
   between 2015 and 2025 is a comparison of reporting systems as well as
   service.
5. **999-minute placeholder.** 1,233 records have exactly 999 delay
   minutes, mostly in 2018. They inflate total delay minutes and the `MSTN`
   location ranking. They were kept under the pre-registered rule.
6. **Missing locations.** 0.08% of records have no usable location and are
   excluded from location rankings. Missingness is unlikely to be random.
7. **Partial final month.** The extract ends on 2026-09-30. The final
   month can be partial in a rolling release, so no trend claim is made
   about it.
8. **Schema break in 2025.** Bus and streetcar switch from `Route`/`Location`
   to `Line`/`Station`, and the delay field is renamed. The harmonisation
   is documented, but a residual coding difference cannot be ruled out.
9. **Model specification.** The logistic model uses line groups, and line
   groups nest inside modes; VIF is high for `line_groupother` and the
   subway line groups. The mode and cause estimates are still stable across
   the robustness checks, but the line-level estimates deserve caution.
10. **Time-based holdout.** 2024 is one year, and its major-delay rate is
    higher than the training period. The calibration result shows the model
    under-predicts 2024; do not treat the AUC as a stable production
    estimate.
11. **No causal claims.** Every model result is an association. The data
    are observational and have no random assignment.
12. **Coverage.** Subway, bus, and streetcar only. No Wheel-Trans, no
    regional transit, and no customer-level outcomes.
