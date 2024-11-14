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

type GetOneResponse struct {
	resp.Response
	Matches models.Matches `json:"match,omitempty"`
}

type OneMatchSelector interface {
	SelectOneMatch(id uint64) (models.Matches, error)
}

func GetOne(log *slog.Logger, oneMatchSelector OneMatchSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.get.GetOne"
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

		match, err := oneMatchSelector.SelectOneMatch(id)
		if err != nil {
			localLog.Error("Failed to select match", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select match"))
			return
		}

		localLog.Info("Selected match", slog.Uint64("match_id", match.Id))

		render.JSON(w, r, GetOneResponse{
			Response: resp.OK(),
			Matches:  match,
		})
		return
	}
}
