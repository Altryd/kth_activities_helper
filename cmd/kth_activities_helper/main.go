package main

import (
	"fmt"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/database"
	"kth_activities_helper/internal/http-server/handlers/match"
	"kth_activities_helper/internal/http-server/handlers/matchType"
	"log/slog"
	"net/http"
	"os"
)

func main() {
	cfg := config.Load()
	fmt.Println(*cfg)

	log := setupLogger(cfg.Env)
	log.Info("Starting backend of kth_activities_helper...", slog.String("env", cfg.Env))

	storage, err := database.New(cfg, log)
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

	router.Get("/api/matches", match.GetAll(log, storage))
	router.Post("/api/match", match.New(log, storage))

	router.Get("/api/matchTypes", matchType.GetAll(log, storage))
	router.Post("/api/matchType", matchType.New(log, storage))

	srv := http.Server{
		Addr:              cfg.HTTPServer.Address,
		Handler:           router,
		ReadHeaderTimeout: cfg.HTTPServer.Timeout,
		WriteTimeout:      cfg.HTTPServer.Timeout,
		IdleTimeout:       cfg.HTTPServer.IdleTimeout,
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
