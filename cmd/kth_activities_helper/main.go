package main

import (
	"fmt"
	"github.com/Altryd/osuParseMpLinks"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/database"
	"kth_activities_helper/internal/http-server/handlers/match"
	"kth_activities_helper/internal/http-server/handlers/matchType"
	matchUser "kth_activities_helper/internal/http-server/handlers/matchUserScrim"
	"kth_activities_helper/internal/http-server/handlers/user"
	"kth_activities_helper/internal/utility"
	"log/slog"
	"net/http"
	"os"
)

/* TODO: переделать с gin либо все-таки вставить этот package
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		jwt_token, err := c.Cookie("jwt")
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		claims, err := security.ValidateToken(jwt_token, "access")

		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}

		c.Set("osuUserId", claims.OsuUserID)
		c.Next()
	}
}
*/

func main() {
	parsingConfig := osuParseMpLinks.ParsingConfig{Debug: true} // TODO: потом удалить, сейчас это нужно, чтобы зависимость не потерялась
	print(parsingConfig.Debug)
	config.Load()
	fmt.Println(config.AppConfig)

	log := setupLogger(config.AppConfig.Env)
	log.Info("Starting backend of kth_activities_helper...", slog.String("env", config.AppConfig.Env))

	storage, err := database.New(log)
	if err != nil {
		os.Exit(-1)
	}

	//id, err := storage.CreateMatchType("MeowMeowMeow")
	//if err != nil {
	//	os.Exit(-1)
	//}
	//log.Info("Inserted MatchType: ", slog.Uint64("id", id))

	router := chi.NewRouter()
	//middleware
	router.Use(middleware.RequestID)
	router.Use(middleware.Recoverer)
	router.Use(middleware.URLFormat)
	router.Use(cors.Handler(cors.Options{ // Чтобы с фронта можно POST послать
		// AllowedOrigins:   []string{"https://foo.com"}, // Use this to allow specific origin hosts
		AllowedOrigins: []string{"https://*", "http://*"},
		// AllowOriginFunc:  func(r *http.Request, origin string) bool { return true },
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: false,
		MaxAge:           300, // Maximum value not ignored by any of major browsers
	}))

	router.Get("/api/matches", match.GetAll(log, storage))
	router.Get("/api/matches/{id}", match.GetOne(log, storage))
	router.Post("/api/match", match.New(log, storage))
	router.Put("/api/matches/{id}/edit", match.Edit(log, storage))
	router.Post("/api/matches/{id}/approve", match.Approve(log, storage))
	router.Post("/api/parse_scrims", match.ParseMatches(log))

	router.Get("/api/create_pairs", match.CreatePairs(log, storage, storage))

	router.Get("/api/matchTypes", matchType.GetAll(log, storage))
	router.Post("/api/matchType", matchType.New(log, storage))

	router.Get("/api/users", user.GetAll(log, storage))
	router.Get("/api/users/{osuId}", user.GetOne(log, storage))
	router.Post("/api/user", user.New(log, storage))
	router.Put("/api/matches/{osuId}/edit", user.EditUser(log, storage))
	router.Get("/api/discord", user.GetDiscordCode(log))
	router.Get("/api/oauth/osu", user.GetOsuCode(log, storage))

	router.Post("/api/match_user", matchUser.New(log, storage))
	matchTypes, err := storage.SelectMatchTypes()
	if err != nil {
		fmt.Printf("Error selecting match types: %v\n", err)
	} else {
		if len(matchTypes) == 0 {
			storage.CreateMatchType("scrim")
			storage.CreateMatchType("weekly")
		}
	}
	err = utility.UploadPlayers("internal/database/golang_players_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading players: %s, skipping", err)
	}
	err = utility.UploadMatches("internal/database/golang_matches_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading matches: %s, skipping", err)
	}
	err = utility.UploadMatchUserScrims("internal/database/golang_match_user_scrim_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading matchUserScrims: %s, skipping", err)
	}

	srv := http.Server{
		Addr:              config.AppConfig.HTTPServer.Address,
		Handler:           router,
		ReadHeaderTimeout: config.AppConfig.HTTPServer.Timeout,
		WriteTimeout:      config.AppConfig.HTTPServer.Timeout,
		IdleTimeout:       config.AppConfig.HTTPServer.IdleTimeout,
	}

	if err := srv.ListenAndServe(); err != nil {
		log.Error("Failed to start server")
	}

	log.Error("Server stopped")
}

const (
	envLocal = "local"
	envDev   = "dev"
	envProd  = "prod"
)

func setupLogger(env string) *slog.Logger {
	var logger *slog.Logger

	switch env {
	case envLocal:
		logger = slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	case envDev:
		logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	case envProd:
		logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	}

	return logger
}
