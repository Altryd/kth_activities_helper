package matchUser

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
)

type Request struct {
	PlayerId uint64 `json:"player_id" validate:"required,gte=0"`
	MatchId  uint64 `json:"match_id" validate:"required,gte=0"`
	Score    uint64 `json:"score" validate:"required,datetime"`
	IsBlue   bool   `json:"is_blue"`
}

type CreateResponse struct {
	resp.Response
	PlayerId uint64 `json:"player_id,omitempty"`
	MatchId  uint64 `json:"match_id,omitempty"`
}

type MatchUserCreator interface {
	CreateMatchUserScrim(playerId uint64, matchId uint64, score uint64, isBlue bool, ratingChange float64) (uint64, uint64, error)
}

func New(log *slog.Logger, MatchUserCreator MatchUserCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.matchUser.create.New"
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
		playerId, matchId, err := MatchUserCreator.CreateMatchUserScrim(req.PlayerId, req.MatchId, req.Score, req.IsBlue, 0.0)
		if err != nil {
			localLog.Error("Failed to create matchUser", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to create matchUser"))
			return
		}

		// TODO delete
		localLog.Info("Created matchUser", slog.Uint64("player_id", playerId),
			slog.Uint64("match_id", matchId))

		render.JSON(w, r, CreateResponse{
			Response: resp.OK(),
			PlayerId: playerId,
			MatchId:  matchId,
		})
		return
	}
}
