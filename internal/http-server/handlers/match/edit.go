package match

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"github.com/go-playground/validator/v10"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"strconv"
	"time"
)

type EditRequest struct {
	// TypeId     uint64    `json:"type_id" validate:"gte=0"`
	FirstPlayerId     uint64    `json:"first_player_id" validate:"gte=0"`
	FirstPlayerScore  uint64    `json:"first_player_score" validate:"gte=0"`
	SecondPlayerId    uint64    `json:"second_player_id" validate:"gte=0"`
	SecondPlayerScore uint64    `json:"second_player_score" validate:"gte=0"`
	Date              time.Time `json:"date" validate:"datetime"`
	// IsApproved bool      `json:"is_approved" validate:"bool"`
}

type EditResponse struct {
	resp.Response
	Match models.Matches `json:"match,omitempty"`
}

type MatchEditor interface {
	EditMatchScrim(matchId uint64, matchDate time.Time, firstPlayerId uint64,
		firstPlayerScore uint64, secondPlayerId uint64, secondPlayerScore uint64) (models.Matches, error)
}

func Edit(log *slog.Logger, matchEditor MatchEditor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.edit.Edit"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		marchId := chi.URLParam(r, "id")
		id, err := strconv.ParseUint(marchId, 10, 64)
		if err != nil {
			http.Error(w, http.StatusText(400), 400)
			return
		}

		var req EditRequest

		err = render.DecodeJSON(r.Body, &req)
		if err != nil {
			localLog.Error("Failed to decode request body")
			render.JSON(w, r, resp.BadRequest("Failed to decode request"))
			return
		}

		if err := validator.New().Struct(req); err != nil {
			validateErr := err.(validator.ValidationErrors)
			localLog.Error("Failed to validate request")
			render.JSON(w, r, resp.ValidationError(validateErr))
			return
		}

		match, err := matchEditor.EditMatchScrim(id, req.Date, req.FirstPlayerId, req.FirstPlayerScore, req.SecondPlayerId, req.SecondPlayerScore)
		if err != nil {
			localLog.Error("Failed to edit match", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to edit match"))
			return
		}

		// TODO delete
		localLog.Info("Edited match", slog.Uint64("match_id", match.Id))

		render.JSON(w, r, EditResponse{
			Response: resp.OK(),
			Match:    match,
		})
		return
	}
}
