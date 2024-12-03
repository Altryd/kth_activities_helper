package match

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"strconv"
)

/*
type ApproveRequest struct {
	TypeId     uint64    `json:"type_id" validate:"required,gte=0"`
	Date       time.Time `json:"date" validate:"required,datetime"`
	IsApproved bool      `json:"is_approved" validate:"required,bool"`
}*/

type ApproveResponse struct {
	resp.Response
	Match models.Matches `json:"match,omitempty"`
}

type MatchApprover interface {
	ApproveMatch(matchId uint64) (models.Matches, error)
}

func Approve(log *slog.Logger, matchApprover MatchApprover) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.edit.Edit"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		matchId := chi.URLParam(r, "id")
		id, err := strconv.ParseUint(matchId, 10, 64)
		if err != nil {
			http.Error(w, http.StatusText(400), 400)
			return
		}

		/*var req EditRequest

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
		}*/

		match, err := matchApprover.ApproveMatch(id)
		if err != nil {
			localLog.Error("Failed to approve match", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to approve match: "))
			return
		}

		// TODO delete
		localLog.Info("Approved match", slog.Uint64("match_id", match.Id))

		render.JSON(w, r, EditResponse{
			Response: resp.OK(),
			Match:    match,
		})
		return
	}
}
