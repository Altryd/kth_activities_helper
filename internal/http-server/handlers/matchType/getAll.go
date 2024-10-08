package matchType

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
	MatchTypes []models.MatchType `json:"match_types,omitempty"`
}

type MatchTypesSelector interface {
	SelectMatchTypes() ([]models.MatchType, error)
}

func GetAll(log *slog.Logger, matchTypesSelector MatchTypesSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.matchType.get.GetAll"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		matchTypes, err := matchTypesSelector.SelectMatchTypes()
		if err != nil {
			localLog.Error("Failed to select all match types", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select all match types"))
		}

		localLog.Info("Selected all match types")

		render.JSON(w, r, GetAllResponse{
			Response:   resp.OK(),
			MatchTypes: matchTypes,
		})
		return
	}
}
