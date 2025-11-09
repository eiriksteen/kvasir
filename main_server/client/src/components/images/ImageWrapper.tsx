import React from "react";
import Image from "next/image";
import { UUID } from "crypto";
import { useImage } from "@/hooks/useImage";

interface ImageWrapperProps {
  imageId: UUID;
  width?: number;
  height?: number;
  className?: string;
  alt?: string;
}

const ImageWrapper = ({ 
  imageId,
  width = 600,
  height = 450,
  className = "w-full h-auto rounded",
  alt = "Analysis image"
}: ImageWrapperProps) => {
  const { imageBlobUrl, isLoading, isError } = useImage(imageId);

  if (isLoading) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-zinc-500 bg-gray-50 rounded">
        Loading image...
      </div>
    );
  }

  if (isError || !imageBlobUrl) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-red-500 bg-gray-50 rounded">
        Failed to load image
      </div>
    );
  }

  return (
    <Image 
      width={width}
      height={height}
      src={imageBlobUrl}
      alt={alt}
      className={className}
      unoptimized
    />
  );
};

export default ImageWrapper;

