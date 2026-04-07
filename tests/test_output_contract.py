from session_designer.domain.output import (
    CandidateTopic,
    SelectedTopic,
    SessionDesignResult,
    SuggestedResource,
    ValidationResult,
)
from session_designer.domain.session_schema import (
    DesignedSession,
    ExtensionSuggestion,
    HandsOnExercise,
    SessionContext,
    SessionGoal,
)


def test_session_design_result_splits_payload_and_metadata() -> None:
    selected = SelectedTopic(
        title="JWT tokens",
        summary="Learn token basics and validation flow.",
        difficulty_alignment="Matches beginner auth level with prior HTTP basics.",
        candidate_id="c2",
    )
    session = DesignedSession(
        goal=SessionGoal(statement="Implement token validation middleware in a sample app."),
        context=SessionContext(
            text="JWT is used to carry claims between client and server with signature validation."
        ),
        hands_on=HandsOnExercise(
            instructions="Build a middleware that parses bearer tokens and validates expiry/signature.",
            expected_output="Protected endpoint returns 200 for valid token and 401 for invalid token.",
            time_estimate_minutes=45,
        ),
        extension=ExtensionSuggestion(
            text="Next: add refresh token rotation and revoke handling."
        ),
        subject_areas=["auth", "jwt", "api"],
    )
    result = SessionDesignResult.from_pipeline(
        selected=selected,
        why_chosen="Natural next step after HTTP foundations.",
        candidates=[
            CandidateTopic(
                id="c2",
                title="JWT tokens",
                one_line_fit="Builds on HTTP knowledge.",
                difficulty_note="Good beginner auth progression.",
                non_repetition_rationale="Moves from transport to identity.",
            )
        ],
        session=session,
        resources=[
            SuggestedResource(
                kind="official_docs",
                title="JWT introduction",
                url="example.com/jwt",
                rationale="Covers token structure and signature checks.",
            )
        ],
        validation=ValidationResult(passed=True),
        revision_count=0,
        normalization_notes=[],
    )

    assert result.session_payload.title == "JWT tokens"
    assert result.session_payload.difficulty_alignment == selected.difficulty_alignment
    assert result.session_payload.subject_areas == ["auth", "jwt", "api"]
    assert result.designer_metadata.why_chosen
    assert result.designer_metadata.selected_candidate_id == "c2"
