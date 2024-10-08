package match

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"github.com/go-playground/validator/v10"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
	"time"
)

type Request struct {
	Id     uint64    `json:"id" validate:"required,gte=0"`
	TypeId uint64    `json:"type_id" validate:"required,gte=0"`
	Date   time.Time `json:"date" validate:"required,datetime"`
}

type CreateResponse struct {
	resp.Response
	MatchId uint64 `json:"match_id,omitempty"`
}

type MatchCreator interface {
	CreateMatch(matchId uint64, matchTypeId uint64, matchDate time.Time) (uint64, error)
}

func New(log *slog.Logger, matchCreator MatchCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.create.New"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		var req Request

		err := render.DecodeJSON(r.Body, &req)
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

		id, err := matchCreator.CreateMatch(req.Id, req.TypeId, req.Date)
		if err != nil {
			localLog.Error("Failed to create match", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to create match"))
		}

		// TODO delete
		localLog.Info("Created match", slog.Uint64("match_id", id))

		render.JSON(w, r, CreateResponse{
			Response: resp.OK(),
			MatchId:  id,
		})
		return
	}
}
