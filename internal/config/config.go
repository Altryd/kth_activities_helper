package config

import (
	"github.com/ilyakaznacheev/cleanenv"
	"log"
	"os"
	"time"
)

type Config struct {
	Env            string `yaml:"env" env:"ENV" env-required:"true"`
	HTTPServer     `yaml:"http_server"`
	DatabaseConfig `yaml:"database_config"`
}

type HTTPServer struct {
	Address     string        `yaml:"address" env:"HTTP_ADDRESS" env-required:"true"`
	Timeout     time.Duration `yaml:"timeout" env:"HTTP_TIMEOUT" env-default:"5s"`
	IdleTimeout time.Duration `yaml:"idle_timeout" env:"HTTP_IDLE_TIMEOUT" env-default:"30s"`
}

type DatabaseConfig struct {
	Address  string `yaml:"address" env:"DB_ADDRESS" env-required:"true"`
	Port     int    `yaml:"port" env:"DB_PORT" env-default:"5432"`
	User     string `yaml:"user" env:"DB_USER" env-required:"true"`
	Pass     string `yaml:"pass" env:"DB_PASS" env-required:"true"`
	Database string `yaml:"database" env:"DB_NAME" env-required:"true"`
	SSLmode  string `yaml:"sslmode" env:"DB_SSLMODE" env-default:"disable"`
}

func Load() *Config {
	configPath := "config\\config.yaml"
	//configPath := os.Getenv("CONFIG_PATH")
	//if configPath == "" {
	//	log.Fatal("CONFIG_PATH environment variable not set")
	//}

	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		log.Fatalf("Config file does not exist: %s", configPath)
	}

	var cfg Config
	if err := cleanenv.ReadConfig(configPath, &cfg); err != nil {
		log.Fatalf("Cannot read config: %s", err)
	}

	return &cfg
}
