package main

import (
	"fmt"
	"math"
)

func GetNewRating(r0 float64, opponentsRating float64, winsFirst int, winsOpponent int, k ...int) float64 {
	kCoef := 35
	if len(k) > 0 {
		kCoef = k[0]
	}
	var G float64 = getG(winsFirst, winsOpponent)

	var W float64 = 0.5
	if winsFirst > winsOpponent {
		W = 1.0
	} else if winsFirst < winsOpponent {
		W = 0
	}
	var We float64 = getWe(r0, opponentsRating)
	return r0 + float64(kCoef)*G*(W-We)
}

func getG(winsFirst int, winsSecond int) float64 {
	var difference float64 = float64(winsFirst) - float64(winsSecond)
	if math.Abs(difference) <= 1.0 {
		return 1.0
	} else if math.Abs(difference) == 2.0 {
		return 3.0 / 2.0
	}
	return (11.0 + math.Abs(difference)) / 8.0
}

func getWe(ratingsFirst float64, ratingsSecond float64) float64 {
	dr := ratingsFirst - ratingsSecond
	denominator := math.Pow(10, (-dr/400)) + 1.0
	return 1 / denominator
}

func main() {
	var ratingA float64 = 630
	var ratingB float64 = 500
	var ratingC float64 = 480
	fmt.Println("First situation: A (rating: 630) 3 vs 1 B (rating: 500)")
	AWins := 3
	BWins := 1
	ratingANew := GetNewRating(ratingA, ratingB, AWins, BWins)
	fmt.Println("difference for A: ", ratingANew-ratingA)
	ratingBNew := GetNewRating(ratingB, ratingA, BWins, AWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)

	fmt.Println("Second situation: A (rating: 630) 1 vs 3 B (rating: 500)")
	AWins = 1
	BWins = 3
	ratingANew = GetNewRating(ratingA, ratingB, AWins, BWins)
	fmt.Println("difference for A: ", ratingANew-ratingA)
	ratingBNew = GetNewRating(ratingB, ratingA, BWins, AWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)

	fmt.Println("Third situation: A (rating: 630) 2 vs 2 B (rating: 500)")
	AWins = 2
	BWins = 2
	ratingANew = GetNewRating(ratingA, ratingB, AWins, BWins)
	fmt.Println("difference for A: ", ratingANew-ratingA)
	ratingBNew = GetNewRating(ratingB, ratingA, BWins, AWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)

	fmt.Println("\n\nteam B vs team C")
	fmt.Println("First situation: B (rat. 500) 3 vs 1 C (rat.480)")
	BWins = 3
	CWins := 1
	ratingBNew = GetNewRating(ratingB, ratingC, BWins, CWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)
	ratingCNew := GetNewRating(ratingC, ratingB, CWins, BWins)
	fmt.Println("difference for C: ", ratingCNew-ratingC)

	fmt.Println("Second situation: B (rat. 500) 1 vs 3 C (rat.480)")
	BWins = 1
	CWins = 3
	ratingBNew = GetNewRating(ratingB, ratingC, BWins, CWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)
	ratingCNew = GetNewRating(ratingC, ratingB, CWins, BWins)
	fmt.Println("difference for C: ", ratingCNew-ratingC)

	fmt.Println("Third situation: B (rat. 500) 2 vs 2 C (rat.480)")
	BWins = 2
	CWins = 2
	ratingBNew = GetNewRating(ratingB, ratingC, BWins, CWins)
	fmt.Println("difference for B: ", ratingBNew-ratingB)
	ratingCNew = GetNewRating(ratingC, ratingB, CWins, BWins)
	fmt.Println("difference for C: ", ratingCNew-ratingC)
}
