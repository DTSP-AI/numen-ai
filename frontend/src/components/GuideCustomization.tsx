"use client";

import React, { useState } from "react";

/**
 * GuideCustomization Component
 *
 * 4 user-facing sliders to customize AI guide personality
 * Maps to 10 backend traits via attribute_calculator.py
 *
 * User Controls → Backend Traits:
 * 1. Guide Energy → assertiveness, confidence, formality
 * 2. Coaching Style → empathy, discipline, supportiveness
 * 3. Creative Expression → creativity, spirituality
 * 4. Communication Depth → verbosity
 *
 * Backend-only (auto-calculated): humor
 */

export interface GuideControls {
  guide_energy: number;          // Calm (0) ↔ Energetic (100)
  coaching_style: number;        // Nurturing (0) ↔ Directive (100)
  creative_expression: number;   // Practical (0) ↔ Imaginative (100)
  communication_depth: number;   // Concise (0) ↔ Detailed (100)
}

interface GuideCustomizationProps {
  onControlsChange?: (controls: GuideControls) => void;
  initialControls?: Partial<GuideControls>;
  disabled?: boolean;
}

const defaultControls: GuideControls = {
  guide_energy: 50,
  coaching_style: 50,
  creative_expression: 50,
  communication_depth: 50,
};

export default function GuideCustomization({
  onControlsChange,
  initialControls,
  disabled = false,
}: GuideCustomizationProps) {
  const [controls, setControls] = useState<GuideControls>({
    ...defaultControls,
    ...initialControls,
  });

  const handleSliderChange = (key: keyof GuideControls, value: number) => {
    const updated = { ...controls, [key]: value };
    setControls(updated);
    onControlsChange?.(updated);
  };

  const sliderConfig = [
    {
      key: "guide_energy" as keyof GuideControls,
      label: "Guide Energy",
      leftLabel: "Calm",
      rightLabel: "Energetic",
      description: "Maps to: Assertiveness, Confidence, Formality",
      emoji: { left: "🧘", right: "⚡" },
    },
    {
      key: "coaching_style" as keyof GuideControls,
      label: "Coaching Style",
      leftLabel: "Nurturing",
      rightLabel: "Directive",
      description: "Maps to: Empathy, Discipline, Supportiveness",
      emoji: { left: "🤗", right: "🎯" },
    },
    {
      key: "creative_expression" as keyof GuideControls,
      label: "Creative Expression",
      leftLabel: "Practical",
      rightLabel: "Imaginative",
      description: "Maps to: Creativity, Spirituality",
      emoji: { left: "📊", right: "✨" },
    },
    {
      key: "communication_depth" as keyof GuideControls,
      label: "Communication Depth",
      leftLabel: "Concise",
      rightLabel: "Detailed",
      description: "Maps to: Verbosity",
      emoji: { left: "💬", right: "📖" },
    },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6 p-6 bg-white rounded-lg shadow-sm">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Customize Your Guide
        </h2>
        <p className="text-sm text-gray-600">
          Adjust these 4 controls to personalize how your guide communicates with you
        </p>
      </div>

      {sliderConfig.map((config) => {
        const value = controls[config.key];
        const percentage = value;

        return (
          <div key={config.key} className="space-y-2">
            {/* Label */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-900">
                {config.label}
              </label>
              <span className="text-xs text-gray-500">{value}</span>
            </div>

            {/* Description */}
            <p className="text-xs text-gray-600 leading-relaxed">
              {config.description}
            </p>

            {/* Slider */}
            <div className="relative pt-2 pb-4">
              {/* Emoji indicators */}
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{config.emoji.left}</span>
                  <span className="text-xs font-medium text-gray-700">
                    {config.leftLabel}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-700">
                    {config.rightLabel}
                  </span>
                  <span className="text-xl">{config.emoji.right}</span>
                </div>
              </div>

              {/* Range input */}
              <input
                type="range"
                min="0"
                max="100"
                value={value}
                disabled={disabled}
                onChange={(e) =>
                  handleSliderChange(config.key, parseInt(e.target.value))
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer
                  disabled:opacity-50 disabled:cursor-not-allowed
                  [&::-webkit-slider-thumb]:appearance-none
                  [&::-webkit-slider-thumb]:w-5
                  [&::-webkit-slider-thumb]:h-5
                  [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-blue-600
                  [&::-webkit-slider-thumb]:cursor-pointer
                  [&::-webkit-slider-thumb]:hover:bg-blue-700
                  [&::-webkit-slider-thumb]:transition-colors
                  [&::-moz-range-thumb]:w-5
                  [&::-moz-range-thumb]:h-5
                  [&::-moz-range-thumb]:rounded-full
                  [&::-moz-range-thumb]:bg-blue-600
                  [&::-moz-range-thumb]:cursor-pointer
                  [&::-moz-range-thumb]:border-0
                  [&::-moz-range-thumb]:hover:bg-blue-700
                  [&::-moz-range-thumb]:transition-colors"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`,
                }}
              />

              {/* Value indicator */}
              <div
                className="absolute top-14 mt-1 transform -translate-x-1/2 transition-all"
                style={{ left: `${percentage}%` }}
              >
                <div className="bg-blue-600 text-white text-xs font-medium px-2 py-1 rounded shadow-sm">
                  {value}
                </div>
              </div>
            </div>
          </div>
        );
      })}

      {/* Info callout */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-100">
        <p className="text-xs text-blue-800 leading-relaxed">
          <strong>💡 Smart Defaults:</strong> These controls are optional. If you skip
          customization, your guide will automatically adapt based on your goals and
          session type using AI-powered trait calculation.
        </p>
      </div>
    </div>
  );
}
