package match

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
)

type GetAllResponse struct {
	resp.Response
	Matches []models.Matches `json:"matches,omitempty"`
}

type MatchesSelector interface {
	SelectMatches() ([]models.Matches, error)
}

func GetAll(log *slog.Logger, matchesSelector MatchesSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.get.GetAll"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		matches, err := matchesSelector.SelectMatches()
		if err != nil {
			localLog.Error("Failed to select all matches", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select all matches"))
		}

		localLog.Info("Selected all matches")

		render.JSON(w, r, GetAllResponse{
			Response: resp.OK(),
			Matches:  matches,
		})
		return
	}
}
