package match

import (
	"encoding/json"
	"fmt"
	"kth_activities_helper/internal/database"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
)

type CreatePairsResponse struct {
	resp.Response
	CreatedPairs  [][]string    `json:"matches,omitempty"` // Изменено на [][]string для соответствия требуемой структуре
	UnusedPlayers []models.User `json:"unused_players,omitempty"`
}

type PairsCreator interface {
	CreatePairs(r *http.Request) (database.Response, int, error)
}

type UserSelector interface {
	SelectUsers() ([]models.User, error)
}

func CreatePairs(log *slog.Logger, userSelector UserSelector, pairsCreator PairsCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.CreatePairs"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		_, err := userSelector.SelectUsers()
		if err != nil {
			localLog.Error("Failed to select all users", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select all users"))
			return
		}

		response, _, err := pairsCreator.CreatePairs(r)
		if err != nil {
			localLog.Error("Failed to create pairs", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to create pairs"))
			return
		}

		localLog.Info("Selected all users")

		err = savePairsToFile(response.CreatedPairs)
		if err != nil {
			localLog.Error("Failed to save pairs to file", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Created pairs but failed to save them"))
			return
		}

		render.JSON(w, r, response)
	}
}

func savePairsToFile(pairs [][]string) error {
	file, err := os.OpenFile("created_pairs.json", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	data, err := json.MarshalIndent(pairs, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal pairs: %w", err)
	}

	if _, err := file.Write(data); err != nil {
		return fmt.Errorf("failed to write data to file: %w", err)
	}

	return nil
}
