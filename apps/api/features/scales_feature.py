"""The rating scale and every constant the web app renders (`GET /scales`), built from `constants/` only."""

from constants.aggregation_constants import (
    AGGREGATION_RULES,
    MEDIAN_OPTIONS,
    METHOD_DESCRIPTIONS,
    METHOD_LABELS,
    AggregationMethod,
)
from constants.band_constants import COUNT_BANDS, VALUE_BANDS
from constants.chart_constants import (
    DEFAULT_NETWORK_LAYOUT,
    NETWORK_LAYOUT_CANVAS,
    NETWORK_LAYOUT_LABELS,
    NETWORK_STYLE,
    PCA_STYLE,
    NetworkLayout,
)
from constants.entropy_constants import ENTROPY_CATEGORIES
from constants.import_constants import IMPORT_SETTINGS
from constants.insights_constants import INSIGHTS_TEXT
from constants.rating_constants import DIAGONAL_LABEL, RATING_FILLS, RATING_LABELS, RATING_SCORES, RATING_TEXT_COLOURS
from models.scale_models import (
    CountBand,
    EntropyCategory,
    ImportScale,
    LayoutOption,
    NetworkScale,
    OptionItem,
    PcaScale,
    RatingScaleItem,
    ScaleRules,
    ScalesData,
    ScaleTexts,
    ValueBand,
)


class ScalesFeature:
    """Publishes the constants."""

    def get_scales(self) -> ScalesData:
        """
        Build the scales.

        Returns:
            ScalesData: Ratings, methods (L1 labels, L2 text), rules, bands, layouts, colours and limits
        """
        rules = AGGREGATION_RULES
        return ScalesData(
            ratings=[
                RatingScaleItem(
                    label=label, score=RATING_SCORES[label], fill=RATING_FILLS[label], text=RATING_TEXT_COLOURS[label]
                )
                for label in RATING_LABELS
            ],
            diagonal_label=DIAGONAL_LABEL,
            methods=[
                OptionItem(key=m.value, label=METHOD_LABELS[m.value], description=METHOD_DESCRIPTIONS[m.value])
                for m in AggregationMethod
            ],
            median_choices=[OptionItem(**option) for option in MEDIAN_OPTIONS],
            rules=ScaleRules(
                min_policies=rules["MIN_POLICIES"],
                max_policies=rules["MAX_POLICIES"],
                min_decision_makers=rules["MIN_DECISION_MAKERS"],
                max_decision_makers=rules["MAX_DECISION_MAKERS"],
                method_choice_min_decision_makers=rules["METHOD_CHOICE_MIN_DECISION_MAKERS"],
                forced_method=rules["FORCED_METHOD"].value,
                default_method=rules["DEFAULT_METHOD"].value,
                default_median_choice=rules["DEFAULT_MEDIAN_CHOICE"].value,
                weight_min=rules["WEIGHT_MIN"],
                weight_max=rules["WEIGHT_MAX"],
                weight_sum_target=rules["WEIGHT_SUM_TARGET"],
                weight_sum_tolerance=rules["WEIGHT_SUM_TOLERANCE"],
            ),
            count_bands=[CountBand(**band) for band in COUNT_BANDS],
            value_bands=[ValueBand(**band) for band in VALUE_BANDS],
            entropy_categories=[EntropyCategory(**category) for category in ENTROPY_CATEGORIES],
            network=NetworkScale(
                layouts=[
                    LayoutOption(key=layout.value, label=NETWORK_LAYOUT_LABELS[layout]) for layout in NetworkLayout
                ],
                default_layout=DEFAULT_NETWORK_LAYOUT.value,
                positive_colour=NETWORK_STYLE["POSITIVE_COLOUR"],
                negative_colour=NETWORK_STYLE["NEGATIVE_COLOUR"],
                isolated_colour=NETWORK_STYLE["ISOLATED_COLOUR"],
                node_colour=NETWORK_STYLE["NODE_COLOUR"],
                focus_colour=NETWORK_STYLE["FOCUS_COLOUR"],
                node_text_colour=NETWORK_STYLE["NODE_TEXT_COLOUR"],
                layout_canvas=list(NETWORK_LAYOUT_CANVAS),
            ),
            pca=PcaScale(point_colour=PCA_STYLE["POINT_COLOUR"], axis_colour=PCA_STYLE["AXIS_COLOUR"]),
            texts=ScaleTexts(most_contested_value_label=INSIGHTS_TEXT["MOST_CONTESTED_VALUE_LABEL"]),
            imports=ImportScale(
                accept=list(IMPORT_SETTINGS["ALLOWED_EXTENSIONS"]), max_bytes=IMPORT_SETTINGS["MAX_UPLOAD_BYTES"]
            ),
        )


scales_feature = ScalesFeature()
