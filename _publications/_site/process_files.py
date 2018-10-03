import sys
from parse_publication import parse_publication

files = [
#    "2002-04-01-determining-land-surface-fractional-cover-from-ndvi-and-rainfall-time-series-for-a-savanna-ecosystem-2.md",  # NOQA
#    "2002-04-06-determining-land-surface-fractional-cover-from-ndvi-and-rainfall-time-series-for-a-savanna-ecosystem.md",  # NOQA
#    "2002-04-22-trends-in-savanna-structure-and-composition-on-an-aridity-gradient-in-the-kalahari.md",  # NOQA
#    "2003-02-13-release-of-gaseous-and-particulate-carbonaceous-compounds-from-biomass-burning-during-the-safari-2000-dry-season-field-campagin.md",  # NOQA
#    "2003-02-14-soil-moisture-and-plant-stress-dynamics-along-the-kalahari-precipitation-gradient.md",  # NOQA
#    "2003-02-19-regional-fuel-load-for-two-climatically-contrasting-years-in-southern-africa.md",  # NOQA
#    "2003-04-22-tree-spacing-along-the-kalahari-transect-in-southern-africa.md",  # NOQA
#    "2003-11-01-structural-characteristics-and-relationships-of-kalahari-woodlands-and-savannas.md",  # NOQA
#    "2004-01-04-a-simulation-analysis-of-the-detectability-of-understory-burns-in-miombo-woodlands.md",  # NOQA
#    "2004-07-07-feasible-optimality-of-vegetation-patterns-in-river-basins.md",  # NOQA
#    "2004-08-27-on-the-coupled-geomorphological-and-ecohydrological-organization-of-river-basins.md",  # NOQA
#    "2004-11-04-relationship-between-small-scale-structural-variability-and-simulated-productivity-across-a-regional-moi-sture-gradient-in-southern-africa.md",  # NOQA
#    "2005-01-07-tree-canopy-effects-on-simulated-water-stress-in-southern-african-savannas.md",  # NOQA
#    "2005-01-11-dynamic-response-of-grass-cover-to-rainfall-variability-implications-for-the-function-and-persistence-of-savanna-ecosystems.md",  # NOQA
#    "2005-07-22-determinants-of-woody-cover-in-african-savannnas-a-continental-scale-analysis.md",  # NOQA
#    "2005-09-22-simulated-productivity-of-heterogeneous-landscape-patches-in-southern-african-savanna-landscapes-using-a-canopy-productivity-model.md",  # NOQA
#    "2006-07-28-on-the-ecohydrological-organization-of-spatially-heterogeneous-semi-arid-landscapes.md",  # NOQA
#    "2007-02-11-when-is-breeding-for-drought-tolerance-optimal-if-drought-is-random.md",  # NOQA
#    "2007-05-04-spatial-variation-in-vegetation-structure-coupled-to-plant-available-water-at-landscape-scales-in-a-brazilian-savanna.md",  # NOQA
#    "2007-07-02-positive-feedbacks-promote-power-law-clustering-of-kalahari-vegetation.md",  # NOQA
#    "2007-09-01-a-temporally-explicit-production-efficiency-model-for-fuel-load-allocation-in-southern-africa.md",  # NOQA
#    "2007-12-08-on-soil-moisture-vegetation-feedbacks-and-their-possible-effects-on-the-dynamics-of-dryland-plant-ecosystems.md",  # NOQA
#    "2008-04-15-spatial-patterns-of-soil-nutrients-in-two-contrasting-southern-african-savannas.md",  # NOQA
#    "2008-12-04-on-the-calibration-of-continuous-high-precision-%ce%b418o-and-%ce%b42h-measurements-using-an-off-axis-integrated-cavity-output-spectrometer.md",  # NOQA
    # "2008-12-12-spatial-heterogeneity-and-sources-of-soil-carbon-in-southern-african-savannas.md",  # NOQA
    # "2009-02-09-on-the-structural-and-environmental-determinants-of-sap-velocity-part-ii-observational-application-2.md",  # NOQA
    # "2009-02-09-on-the-structural-and-environmental-determinants-of-sap-velocity-part-ii-observational-application.md",  # NOQA
    # "2009-02-25-ecohydrological-optimization-of-pattern-and-processes-in-water-limited-ecosystems-a-tradeoff-based-hypothesis.md",  # NOQA
    # "2009-07-07-combined-effects-of-soil-moisture-and-nitrogen-availability-on-grass-productivity-in-african-savannas.md",  # NOQA
    # "2009-10-27-nutrient-limitation-on-above-ground-grass-production-in-four-savanna-types-along-the-kalahari-transect.md",  # NOQA
    # "2009-12-04-on-the-importance-of-accurate-depiction-of-infiltration-processes-on-modelled-soil-moisture-and-vegetation-water-stress.md",  # NOQA
    # "2010-01-06-an-ecohydrological-approach-to-predicting-regional-species-distribution-patterns-in-dryland-ecosystems.md",  # NOQA
    # "2010-05-07-partitioning-evapotranspiration-across-gradients-of-woody-plant-cover-assessment-of-a-stable-isotope-technique.md",  # NOQA
    # "2010-06-04-herbivores-and-mutualistic-ants-interact-to-modify-tree-photosynthesis.md",  # NOQA
    # "2011-01-19-quantifying-transient-soil-moisture-dynamics-using-multi-point-direct-current-resistivity-in-homogeneous-sand.md",  # NOQA
    # "2011-03-15-climatological-determinants-of-woody-cover-in-africa.md",  # NOQA
    # "2011-06-14-metabolic-principles-of-river-basin-organization.md",  # NOQA
    # "2011-07-01-ecohydrology-in-practice.md",  # NOQA
    # "2011-07-30-understanding-ecohydrological-feedbacks.md",  # NOQA
    # "2012-01-02-predicting-hillslope-scale-vegetation-patterns-in-dryland-ecosystems.md",  # NOQA
    # "2012-01-17-characterizing-ecohydrological-and-biogeochemical-connectivity-across-multiple-scales-a-new-conceptual-framework.md",  # NOQA
    # "2012-01-23-direct-quantification-of-leaf-transpiration-isotopic-composition.md",  # NOQA
    # "2012-03-28-evaluating-ecohydrological-theories-of-woody-root-distribution-in-the-kalahari.md",  # NOQA
    # "2012-05-04-odonnell-jgr-biogeosciences.md",  # NOQA
    # "2012-07-17-multi-sensor-derivation-of-regional-vegetation-fractional-cover-in-africa.md",  # NOQA
    # "2012-08-01-uncertainties-in-the-assessment-of-the-isotopic-composition-of-surface-fluxes-a-direct-comparison-of-techniques-using-laser-based-water-vapor-isotope-analyzers.md",  # NOQA
    # "2012-08-09-dryland-ecohydrology-and-climate-change-critical-issues-and-technical-advances.md",  # NOQA
    # "2012-09-12-stable-isotopes-of-water-vapor-in-the-vadose-zone-a-review-of-measurement-and-modeling-techniques.md",  # NOQA
    # "2012-11-06-reframing-hydrology-education-to-solve-coupled-human-and-environmental-problems.md",  # NOQA
#    "2013-03-11-using-atmospheric-trajectories-to-model-the-isotopic-composition-of-rainfall-in-central-kenya.md",  # NOQA
    # "2013-03-18-seasonal-coupling-of-canopy-structure-and-function-in-african-tropical-forests-and-its-environmental-controls.md",  # NOQA
    # "2013-04-23-the-effect-of-warming-on-grassland-evapotranspiration-partitioning-using-laser-based-isotope-monitoring-techniques.md",  # NOQA
    # "2013-05-08-analytical-expressions-of-variability-in-ecosystem-structure-and-function-obtained-from-three-dimensional-stochastic-vegetation-modelling.md",  # NOQA
    # "2013-08-06-projected-impacts-maize-wheat-production.md",  # NOQA
    # "2014-01-10-ecosystem-scale-spatial-heterogeneity-of-stable-isotopes-of-soil-nitrogen-in-african-savannas.md",  # NOQA
#    "2014-01-10-modelling-vegetation-patterns-in-semiarid-environments-2.md",  # NOQA
    # "2014-01-10-on-the-vulnerability-of-water-limited-ecosystems-to-climate-change.md",  # NOQA
    # "2014-01-10-virtual-water-trade-and-development-in-africa.md",  # NOQA
    # "2014-01-23-using-changes-in-agricultural-utility-to-quantify-future-climate-induced-risk-to-conservation.md",  # NOQA
    # "2014-08-19-an-analysis-of-structure-2014.md",  # NOQA
    # "2014-08-19-deriving-vegetation-phenological-time-and-trajectory-information-over-africa-using-seviri-daily-lai.md",  # NOQA
    # "2014-08-19-isotopic-flux-partitioning-2014.md",  # NOQA
    # "2014-10-02-global-synthesis-of-vegetation-control-on-evapotranspiration-partitioning.md",  # NOQA
    # "2014-12-11-continental-scale-impacts-of-intra-seasonal-rainfall-variability-on-simulated-ecosystem-responses-in-africa.md",  # NOQA
    # "2015-02-09-termite-mounds-can-increase-the-robustness-of-dryland-ecosystems-to-climatic-change.md",  # NOQA
    # "2015-03-10-photosynthetic-seasonality-of-global-tropical-forests-constrained-by-hydroclimate.md",  # NOQA
    # "2015-03-16-high-carbon-and-biodiversity-costs-from-converting-africas-wet-savannas-to-cropland.md",  # NOQA
    # "2015-04-14-carbon-stable-isotopes-suggest-that-hippopotamus-vectored-nutrients-subsidize-aquatic-consumers-in-an-east-african-river.md",  # NOQA
    # "2015-08-03-pervasive-drought-legacies-in-forest-ecosystems-and-their-implications-for-carbon-cycle-models.md",  # NOQA
    # "2015-08-25-dynamic-interactions-of-ecohydrological-and-biogeochemical-processes-in-water-limited-systems.md",  # NOQA
    # "2015-09-24-a-quantitative-description-of-the-interspecies-diversity-of-belowground-structure-in-savanna-woody-plants.md",  # NOQA
    # "2016-02-14-improved-removal-of-volatile-organic-compounds-for-laser-based-spectroscopy-of-water-isotopes.md",  # NOQA
    # "2016-04-11-a-generalized-computer-vision-approach-to-mapping-crop-fields-in-heterogeneous-agricultural-landscapes.md",  # NOQA
    # "2016-08-08-reconciling-agriculture-carbon-and-biodiversity-in-a-savannah-transformation-frontier.md",  # NOQA
     "2016-11-11-4779.md"  # NOQA
]

if len(sys.argv) > 1:
    filename = sys.argv[1]  # File name to parse
else:
    for file in files:
        if input("Parse {file}?".format(file=file)):
            parse_publication(file)
